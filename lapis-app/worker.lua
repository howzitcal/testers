-- Run with: resty /app/worker.lua
-- Mirrors Go/Bun worker: drain background_jobs + health/dummy every 1s

local mysql = require("resty.mysql")
local cjson = require("cjson.safe")

local function getenv(key, fallback)
  local v = os.getenv(key)
  if v and v ~= "" then
    return v
  end
  return fallback
end

local cfg = {
  host = getenv("DB_HOST", "host.docker.internal"),
  port = tonumber(getenv("DB_PORT", "3306")),
  user = getenv("DB_USERNAME", "root"),
  password = getenv("DB_PASSWORD", "password"),
  database = getenv("DB_NAME", "lapis_leads"),
}

local JOB_WELCOME_EMAIL = "welcome_email"

local function connect()
  local db, err = mysql:new()
  if not db then
    return nil, err
  end
  db:set_timeout(5000)
  local ok
  ok, err = db:connect({
    host = cfg.host,
    port = cfg.port,
    user = cfg.user,
    password = cfg.password,
    database = cfg.database,
    charset = "utf8mb4",
  })
  if not ok then
    return nil, err
  end
  return db
end

local function q(db, sql)
  return db:query(sql)
end

local function send_mock_mail(to_name, to_email, subject, body)
  ngx.log(ngx.NOTICE, string.format(
    "[MOCK MAIL] to=%s <%s> subject=%q body=%q",
    to_name, to_email, subject, body
  ))
end

local function run_health_check()
  local db, err = connect()
  if not db then
    ngx.log(ngx.ERR, "health check connect: ", err)
    return
  end
  local res
  res, err = q(db, "SELECT COUNT(*) AS n FROM leads")
  if not res then
    ngx.log(ngx.ERR, "health check count: ", err)
    db:close()
    return
  end
  local n = tonumber(res[1].n) or 0
  local msg = "System health check OK — lead count=" .. n
  local ok
  ok, err = q(db, "INSERT INTO audit_log (message) VALUES (" .. ngx.quote_sql_str(msg) .. ")")
  if not ok then
    ngx.log(ngx.ERR, "health check audit: ", err)
  else
    ngx.log(ngx.NOTICE, msg)
  end
  db:close()
end

local function dummy_job()
  ngx.log(ngx.NOTICE, "dummy job")
end

local function claim_next_job(db)
  local ok, err = q(db, "START TRANSACTION")
  if not ok then
    return nil, err
  end
  local res
  res, err = q(db, [[
    SELECT id, job_type, payload, status
    FROM background_jobs
    WHERE status = 'pending'
    ORDER BY id
    LIMIT 1
    FOR UPDATE
  ]])
  if not res then
    q(db, "ROLLBACK")
    return nil, err
  end
  if #res == 0 then
    q(db, "ROLLBACK")
    return nil
  end
  local job = res[1]
  ok, err = q(db, string.format(
    "UPDATE background_jobs SET status = 'running', started_at = UTC_TIMESTAMP(6) WHERE id = %d",
    tonumber(job.id)
  ))
  if not ok then
    q(db, "ROLLBACK")
    return nil, err
  end
  ok, err = q(db, "COMMIT")
  if not ok then
    return nil, err
  end
  job.status = "running"
  return job
end

local function handle_job(job)
  if job.job_type ~= JOB_WELCOME_EMAIL then
    error("unknown job_type: " .. tostring(job.job_type))
  end
  local payload = cjson.decode(job.payload) or {}
  ngx.log(ngx.NOTICE, string.format(
    "Processing welcome_email job id=%s lead_id=%s",
    tostring(job.id), tostring(payload.lead_id)
  ))
  ngx.sleep(0.5)
  send_mock_mail(
    payload.name or "",
    payload.email or "",
    "Welcome!",
    "Thanks for signing up, " .. (payload.name or "") .. "."
  )
end

ngx.log(ngx.NOTICE, "Lapis worker started (MySQL queue + schedules every 1s)")

local last_sched = 0
while true do
  local now = ngx.now()
  if now - last_sched >= 1 then
    last_sched = now
    run_health_check()
    dummy_job()
  end

  local db, err = connect()
  if not db then
    ngx.log(ngx.ERR, "claim connect: ", err)
    ngx.sleep(1)
  else
    local job
    job, err = claim_next_job(db)
    if err then
      ngx.log(ngx.ERR, "claim job: ", err)
      db:close()
      ngx.sleep(1)
    elseif not job then
      db:close()
      ngx.sleep(1)
    else
      local ok, herr = pcall(handle_job, job)
      if not ok then
        ngx.log(ngx.ERR, "Job id=", job.id, " failed: ", herr)
        q(db, string.format(
          "UPDATE background_jobs SET status = 'failed', error = %s, finished_at = UTC_TIMESTAMP(6) WHERE id = %d",
          ngx.quote_sql_str(tostring(herr)),
          tonumber(job.id)
        ))
      else
        q(db, string.format(
          "UPDATE background_jobs SET status = 'done', finished_at = UTC_TIMESTAMP(6) WHERE id = %d",
          tonumber(job.id)
        ))
      end
      db:close()
    end
  end
end

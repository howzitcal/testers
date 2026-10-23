local Model = require("lapis.db.model").Model
local db = require("lapis.db")
local cjson = require("cjson")

local Leads = Model:extend("leads", {
  primary_key = "id",
})

local AuditLog = Model:extend("audit_log", {
  primary_key = "id",
})

local BackgroundJobs = Model:extend("background_jobs", {
  primary_key = "id",
})

local STATUSES = { "new", "contacted", "qualified" }
local JOB_WELCOME_EMAIL = "welcome_email"

local function valid_status(status)
  for _, s in ipairs(STATUSES) do
    if s == status then
      return status
    end
  end
  return "new"
end

local function list_leads()
  return Leads:select("ORDER BY id ASC")
end

local function get_lead(id)
  return Leads:find(tonumber(id))
end

local function create_lead(name, email, status)
  return Leads:create({
    name = name,
    email = email,
    status = valid_status(status),
  })
end

local function update_lead(lead, name, email, status)
  lead:update({
    name = name,
    email = email,
    status = valid_status(status),
  })
  return lead
end

local function delete_lead(lead)
  lead:delete()
end

local function count_leads()
  local rows = db.select("COUNT(*) AS n FROM leads")
  local row = rows and rows[1]
  return tonumber(row and row.n or 0)
end

local function create_audit_log(message)
  return AuditLog:create({ message = message })
end

local function enqueue_welcome_email(lead)
  return BackgroundJobs:create({
    job_type = JOB_WELCOME_EMAIL,
    payload = cjson.encode({
      lead_id = lead.id,
      name = lead.name,
      email = lead.email,
    }),
    status = "pending",
  })
end

return {
  STATUSES = STATUSES,
  JOB_WELCOME_EMAIL = JOB_WELCOME_EMAIL,
  Leads = Leads,
  list_leads = list_leads,
  get_lead = get_lead,
  create_lead = create_lead,
  update_lead = update_lead,
  delete_lead = delete_lead,
  count_leads = count_leads,
  create_audit_log = create_audit_log,
  enqueue_welcome_email = enqueue_welcome_email,
  valid_status = valid_status,
}

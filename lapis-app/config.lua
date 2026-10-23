local config = require("lapis.config")

local function mysql_cfg()
  return {
    host = os.getenv("DB_HOST") or "host.docker.internal",
    port = tonumber(os.getenv("DB_PORT") or "3306"),
    user = os.getenv("DB_USERNAME") or "root",
    password = os.getenv("DB_PASSWORD") or "password",
    database = os.getenv("DB_NAME") or "lapis_leads",
  }
end

config("development", {
  port = tonumber(os.getenv("HTTP_PORT") or "8009"),
  num_workers = 1,
  code_cache = "off",
  mysql = mysql_cfg(),
})

config("production", {
  port = tonumber(os.getenv("HTTP_PORT") or "8009"),
  num_workers = 1,
  code_cache = "on",
  mysql = mysql_cfg(),
})

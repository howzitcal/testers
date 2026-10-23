local lapis = require("lapis")
local models = require("models")

local app = lapis.Application()
app:enable("etlua")
app.layout = require("views.layout")

local function validate(name, email, status)
  local errors = {}
  if not name or name == "" then
    errors.name = "Name is required"
  end
  if not email or email == "" then
    errors.email = "Email is required"
  end
  status = models.valid_status(status or "new")
  return status, errors
end

app:get("index", "/", function(self)
  self.leads = models.list_leads()
  self.message = self.params.msg
  self.title = "Lapis Leads"
  return { render = "list" }
end)

app:match("/leads/new", function(self)
  self.title = "New Lead"
  self.statuses = models.STATUSES

  if self.req.method == "POST" then
    local name = (self.params.name or ""):match("^%s*(.-)%s*$")
    local email = (self.params.email or ""):match("^%s*(.-)%s*$")
    local status, errors = validate(name, email, self.params.status)
    if next(errors) then
      self.lead = { name = name, email = email, status = status }
      self.errors = errors
      return { render = "form" }
    end
    local lead = models.create_lead(name, email, status)
    models.enqueue_welcome_email(lead)
    return {
      redirect_to = self:url_for("index")
        .. "?msg="
        .. ngx.escape_uri("Lead created; welcome email queued."),
    }
  end

  self.lead = { name = "", email = "", status = "new" }
  self.errors = {}
  return { render = "form" }
end)

app:match("/leads/:id/edit", function(self)
  local lead = models.get_lead(self.params.id)
  if not lead then
    return { status = 404, render = false, layout = false }, "Not found"
  end

  self.title = "Edit Lead"
  self.statuses = models.STATUSES

  if self.req.method == "POST" then
    local name = (self.params.name or ""):match("^%s*(.-)%s*$")
    local email = (self.params.email or ""):match("^%s*(.-)%s*$")
    local status, errors = validate(name, email, self.params.status)
    if next(errors) then
      self.lead = { id = lead.id, name = name, email = email, status = status }
      self.errors = errors
      return { render = "form" }
    end
    models.update_lead(lead, name, email, status)
    return {
      redirect_to = self:url_for("index") .. "?msg=" .. ngx.escape_uri("Lead updated."),
    }
  end

  self.lead = lead
  self.errors = {}
  return { render = "form" }
end)

app:post("/leads/:id/delete", function(self)
  local lead = models.get_lead(self.params.id)
  if lead then
    models.delete_lead(lead)
  end
  return {
    redirect_to = self:url_for("index") .. "?msg=" .. ngx.escape_uri("Lead deleted."),
  }
end)

return app

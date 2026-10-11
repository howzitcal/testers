from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config

from .jobs import enqueue_welcome_email
from .models import Lead

STATUSES = ("new", "contacted", "qualified")


@view_config(route_name="lead_list", renderer="list.jinja2")
def lead_list(request):
    leads = request.dbsession.query(Lead).order_by(Lead.id).all()
    return {"leads": leads, "message": request.GET.get("msg")}


@view_config(route_name="lead_create", renderer="form.jinja2", request_method="GET")
def lead_create_form(request):
    return {"lead": None, "title": "New Lead", "statuses": STATUSES, "errors": {}}


@view_config(route_name="lead_create", renderer="form.jinja2", request_method="POST")
def lead_create(request):
    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    status = (request.POST.get("status") or "new").strip()
    errors = {}
    if not name:
        errors["name"] = "Name is required"
    if not email:
        errors["email"] = "Email is required"
    if status not in STATUSES:
        status = "new"
    if errors:
        return {
            "lead": {"name": name, "email": email, "status": status},
            "title": "New Lead",
            "statuses": STATUSES,
            "errors": errors,
        }

    lead = Lead(name=name, email=email, status=status)
    request.dbsession.add(lead)
    request.dbsession.flush()

    enqueue_welcome_email(request.dbsession, lead.id, lead.name, lead.email)

    return HTTPFound(location=request.route_url("lead_list", _query={"msg": "Lead created; welcome email queued."}))


@view_config(route_name="lead_edit", renderer="form.jinja2", request_method="GET")
def lead_edit_form(request):
    lead = request.dbsession.get(Lead, int(request.matchdict["id"]))
    if lead is None:
        raise HTTPNotFound()
    return {"lead": lead, "title": "Edit Lead", "statuses": STATUSES, "errors": {}}


@view_config(route_name="lead_edit", renderer="form.jinja2", request_method="POST")
def lead_edit(request):
    lead = request.dbsession.get(Lead, int(request.matchdict["id"]))
    if lead is None:
        raise HTTPNotFound()

    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    status = (request.POST.get("status") or "new").strip()
    errors = {}
    if not name:
        errors["name"] = "Name is required"
    if not email:
        errors["email"] = "Email is required"
    if status not in STATUSES:
        status = "new"
    if errors:
        lead.name = name
        lead.email = email
        lead.status = status
        return {"lead": lead, "title": "Edit Lead", "statuses": STATUSES, "errors": errors}

    lead.name = name
    lead.email = email
    lead.status = status
    return HTTPFound(location=request.route_url("lead_list", _query={"msg": "Lead updated."}))


@view_config(route_name="lead_delete", request_method="POST")
def lead_delete(request):
    lead = request.dbsession.get(Lead, int(request.matchdict["id"]))
    if lead is None:
        raise HTTPNotFound()
    request.dbsession.delete(lead)
    return HTTPFound(location=request.route_url("lead_list", _query={"msg": "Lead deleted."}))

import os

from pyramid.config import Configurator

from .models import Base, get_engine, get_session_factory, get_tm_session


def main(global_config, **settings):
    """Web-only app factory — no in-process worker or scheduler."""
    os.makedirs("data", exist_ok=True)

    # Prefer env override (Docker) when present
    db_url = os.environ.get("SQLALCHEMY_URL") or settings.get("sqlalchemy.url")
    if db_url:
        settings["sqlalchemy.url"] = db_url

    engine = get_engine(settings["sqlalchemy.url"])
    Base.metadata.create_all(engine)
    session_factory = get_session_factory(engine)

    config = Configurator(settings=settings)
    config.include("pyramid_jinja2")
    config.include("pyramid_tm")

    config.registry["db_session_factory"] = session_factory

    def db(request):
        return get_tm_session(session_factory, request.tm)

    config.add_request_method(db, "dbsession", reify=True)

    config.add_route("lead_list", "/")
    config.add_route("lead_create", "/leads/new")
    config.add_route("lead_edit", "/leads/{id}/edit")
    config.add_route("lead_delete", "/leads/{id}/delete")
    config.scan(".views")

    return config.make_wsgi_app()

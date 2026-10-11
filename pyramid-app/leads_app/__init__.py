import atexit
import os

from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .background import WelcomeEmailWorker
from .models import Base, get_session_factory, get_tm_session
from .scheduler import start_scheduler


def main(global_config, **settings):
    os.makedirs("data", exist_ok=True)

    engine = engine_from_config(settings, prefix="sqlalchemy.")
    Base.metadata.create_all(engine)
    session_factory = get_session_factory(engine)

    worker = WelcomeEmailWorker()
    worker.start()

    config = Configurator(settings=settings)
    config.include("pyramid_jinja2")
    config.include("pyramid_tm")

    config.registry["db_session_factory"] = session_factory
    config.registry["welcome_worker"] = worker

    def db(request):
        return get_tm_session(session_factory, request.tm)

    config.add_request_method(db, "dbsession", reify=True)

    config.add_route("lead_list", "/")
    config.add_route("lead_create", "/leads/new")
    config.add_route("lead_edit", "/leads/{id}/edit")
    config.add_route("lead_delete", "/leads/{id}/delete")
    config.scan(".views")

    scheduler = start_scheduler(settings, engine)
    config.registry["scheduler"] = scheduler

    def _shutdown():
        worker.stop()
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

    atexit.register(_shutdown)

    return config.make_wsgi_app()

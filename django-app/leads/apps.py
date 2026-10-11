from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "leads"

    def ready(self):
        # Ensure data directory exists for SQLite
        from pathlib import Path

        from django.conf import settings

        Path(settings.DATABASES["default"]["NAME"]).parent.mkdir(parents=True, exist_ok=True)
        from . import signals  # noqa: F401

from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "leads"

    def ready(self):
        from . import signals  # noqa: F401

        # Ensure 1s schedules exist even without a fresh migrate
        try:
            from .tasks import ensure_health_check_schedule

            ensure_health_check_schedule()
        except Exception:
            # DB / django_q tables may not be ready during first boot
            pass

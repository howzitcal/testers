from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_health_check_schedule(sender, **kwargs):
    if sender.name != "leads":
        return
    try:
        from .tasks import ensure_health_check_schedule

        ensure_health_check_schedule()
    except Exception:
        # django_q tables may not exist yet on first migrate of django_q itself
        pass

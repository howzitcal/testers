from django.core.management.base import BaseCommand

from leads.tasks import run_health_check


class Command(BaseCommand):
    help = "Run the system health check and write an audit_log row."

    def handle(self, *args, **options):
        message = run_health_check()
        self.stdout.write(self.style.SUCCESS(message))

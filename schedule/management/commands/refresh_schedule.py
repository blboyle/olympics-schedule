from django.core.management.base import BaseCommand

from schedule.scraper import fetch_all_schedule


class Command(BaseCommand):
    help = "Refresh Olympics schedule from API"

    def handle(self, *args, **options):
        self.stdout.write("Refreshing Olympics schedule...")
        try:
            count = fetch_all_schedule()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully fetched {count} events")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            raise

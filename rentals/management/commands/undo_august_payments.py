from django.core.management.base import BaseCommand
from datetime import date
from rentals.models import Payment

class Command(BaseCommand):
    help = 'Delete all simulated payments for August 2025'

    def handle(self, *args, **kwargs):
        august_start = date(2025, 8, 1)
        august_end = date(2025, 8, 31)

        deleted_count, _ = Payment.objects.filter(
            payment_date__range=(august_start, august_end),
            notes="Simulated August payment"
        ).delete()

        self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_count} August 2025 payments."))

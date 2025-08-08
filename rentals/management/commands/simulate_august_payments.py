import random
from datetime import timedelta, date, datetime
from django.core.management.base import BaseCommand
from rentals.models import Tenant, Payment
from decimal import Decimal

class Command(BaseCommand):
    help = 'Simulate August payments where most tenants clear debts'

    def handle(self, *args, **kwargs):
        tenants = Tenant.objects.all()
        august_1 = date.today().replace(day=1, month=8)
        methods = ['mpesa', 'cash', 'bank_transfer']

        for tenant in tenants:
            # Skip if lease hasn't started yet
            if tenant.lease_start_date > august_1:
                continue

            rent_amount = tenant.unit.rent_amount
            rand = random.random()

            if rand < 0.1:
                amount = Decimal('0.00')  # Unpaid
            elif rand < 0.2:
                amount = rent_amount * Decimal('0.5')  # Partial
            else:
                amount = rent_amount  # Most clear full rent

            Payment.objects.create(
                tenant=tenant,
                amount=amount,
                payment_date=august_1,
                payment_method=random.choice(methods),
                reference_number=f"TX-{random.randint(10000, 99999)}",
                notes="August payment - simulated"
            )

        self.stdout.write(self.style.SUCCESS('August payments simulated successfully.'))

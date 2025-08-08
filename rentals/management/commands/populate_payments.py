import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from rentals.models import Tenant, Payment
from decimal import Decimal

class Command(BaseCommand):
    help = 'Simulate realistic payments from lease start to August 2025'

    def handle(self, *args, **kwargs):
        tenants = Tenant.objects.all()
        methods = ['mpesa', 'cash', 'bank_transfer']
        august_1st = date(2025, 8, 1)

        for tenant in tenants:
            rent = tenant.unit.rent_amount
            start = tenant.lease_start_date
            months = (august_1st.year - start.year) * 12 + (august_1st.month - start.month)

            for m in range(months + 1):
                pay_date = start + timedelta(days=m * 30)
                if pay_date > august_1st:
                    continue

                # Simulate payment behavior
                if m == months:  # August payment
                    rand = random.random()
                    if rand < 0.7:
                        amount = rent  # Most tenants fully paid
                    elif rand < 0.9:
                        amount = rent * Decimal('0.5')  # Partial
                    else:
                        amount = Decimal('0.00')  # Missed
                else:
                    rand = random.random()
                    if rand < 0.05:
                        amount = Decimal('0.00')  # Missed
                    elif rand < 0.2:
                        amount = rent * Decimal('0.5')  # Partial
                    elif rand < 0.85:
                        amount = rent  # Full
                    else:
                        amount = rent + Decimal(random.randint(500, 2000))  # Overpayment

                Payment.objects.create(
                    tenant=tenant,
                    amount=amount,
                    payment_date=pay_date,
                    payment_method=random.choice(methods),
                    reference_number=f"TX-{random.randint(10000, 99999)}",
                    notes="Simulated payment"
                )

        self.stdout.write(self.style.SUCCESS('Realistic payments populated through August 2025.'))


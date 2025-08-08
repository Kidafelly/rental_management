import random
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from faker import Faker
from datetime import date, datetime, timedelta

from rentals.models import Unit, Tenant

fake = Faker()

class Command(BaseCommand):
    help = 'Populate tenants and assign them to available units'

    def handle(self, *args, **kwargs):
        vacant_units = Unit.objects.filter(status='vacant')
        tenant_count = 0

        for unit in vacant_units:
            start_date = fake.date_between_dates(date_start=date(2025, 1, 1), date_end=date(2025, 8, 2))
            end_date = start_date.replace(year=start_date.year + 1)
            created_at = make_aware(fake.date_time_between(start_date='-7M', end_date='now'))

            tenant = Tenant.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                phone_number="+2547{}".format(random.randint(10000000, 99999999)),
                unit=unit,
                lease_start_date=start_date,
                lease_end_date=end_date,
                security_deposit=random.randint(10000, 20000),
                created_at=created_at,
                payment_status=random.choice(['paid', 'unpaid', 'partial', 'overdue'])
            )

            self.stdout.write(f"✓ Created tenant {tenant.full_name} in {unit.unit_number}")
            tenant_count += 1

        self.stdout.write(self.style.SUCCESS(f"🏠 {tenant_count} tenants created and assigned to vacant units."))

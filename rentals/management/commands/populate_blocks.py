import random
from django.core.management.base import BaseCommand
from rentals.models import Block, Unit

class Command(BaseCommand):
    help = "Populates initial blocks and units"

    def handle(self, *args, **kwargs):
        unit_types = [
            ('Studio', 10000),
            ('1 Bedroom', 15000),
            ('2 Bedroom', 20000),
            ('3 Bedroom', 25000),
            ('4 Bedroom', 30000),
        ]

        blocks = [
            {
                "name": "South B Apartment",
                "units": 63,
                "location": "South B, Nairobi",
                "manager": "John Doe",
                "description": "Spacious apartments ideal for families near shopping centers."
            },
            {
                "name": "Kilimani Flats",
                "units": 13,
                "location": "Kilimani, Nairobi",
                "manager": "Jane Smith",
                "description": "Modern city flats with parking and security."
            },
            {
                "name": "Fedha Apartment",
                "units": 81,
                "location": "Fedha Estate, Embakasi",
                "manager": "Alex Mwangi",
                "description": "Affordable units with reliable water and electricity."
            },
        ]

        for block_data in blocks:
            block, created = Block.objects.get_or_create(
                name=block_data["name"],
                defaults={
                    "location": block_data["location"],
                    "manager": block_data["manager"],
                    "description": block_data["description"],
                    "total_units": block_data["units"],
                }
            )

            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Exists'} block: {block.name}"
            ))

            # Force unit creation regardless of block existence
            if True:
                for i in range(1, block_data["units"] + 1):
                    unit_type, rent = random.choice(unit_types)
                    unit_number = f"{block.name[:2].upper()}{i}"
                    Unit.objects.create(
                        block=block,
                        unit_number=unit_number,
                        unit_type=unit_type,
                        rent_amount=rent,
                        description=f"{unit_type} in {block.name}, KES {rent:,}",
                    )
                self.stdout.write(f"  → {block_data['units']} units created under {block.name}")

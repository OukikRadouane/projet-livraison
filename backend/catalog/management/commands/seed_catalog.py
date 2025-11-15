from django.core.management.base import BaseCommand
from catalog.models import Item

DEFAULT_ITEMS = [
    ("Pomme", "FRUIT", "kg", 1.0),
    ("Banane", "FRUIT", "kg", 1.0),
    ("Orange", "FRUIT", "kg", 1.0),
    ("Tomate", "VEGETABLE", "kg", 1.0),
    ("Pomme de terre", "VEGETABLE", "kg", 1.0),
    ("Oignon", "VEGETABLE", "kg", 1.0),
    ("Pizza Margherita", "PREPARED", "unit", 0.5),
]


class Command(BaseCommand):
    help = "Seed example catalog items"

    def handle(self, *args, **options):
        created = 0
        for name, category, unit, w in DEFAULT_ITEMS:
            obj, was_created = Item.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "unit": unit,
                    "weight_per_unit_kg": w,
                },
            )
            created += 1 if was_created else 0
        self.stdout.write(self.style.SUCCESS(f"Seeded items. Created: {created}"))

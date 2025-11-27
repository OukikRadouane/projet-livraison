from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order, OrderItem
from catalog.models import Item


class Command(BaseCommand):
    help = "Seed sample pending orders for testing courier lists"

    def handle(self, *args, **options):
        items = list(Item.objects.all())
        if not items:
            self.stdout.write(self.style.WARNING("No catalog items found. Please run catalog seeder first."))
            return

        samples = [
            {"phone": "+212600000001", "lat": 33.5731, "lng": -7.5898, "price": 20.0},  # Casablanca
            {"phone": "+212600000002", "lat": 33.5899, "lng": -7.6039, "price": 15.0},
            {"phone": "+212600000003", "lat": 33.5600, "lng": -7.6200, "price": 25.0},
        ]

        created = 0
        for s in samples:
            o = Order.objects.create(
                customer_phone=s["phone"],
                location_lat=s["lat"],
                location_lng=s["lng"],
                delivery_price_offer=s["price"],
                status=Order.Status.PENDING,
            )
            # Attach 1-2 random items
            for it in items[:2]:
                OrderItem.objects.create(order=o, item=it, quantity=1)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} pending orders."))

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from catalog.models import Item
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create 10 test clients with distributed orders around Casablanca'

    def handle(self, *args, **options):
        # Casablanca coordinates and surrounding areas
        locations = [
            (33.5731, -7.5898, "Centre-ville"),
            (33.5950, -7.6150, "Maarif"),
            (33.5500, -7.6200, "Ain Diab"),
            (33.6100, -7.5700, "Sidi Moumen"),
            (33.5400, -7.5500, "Hay Hassani"),
            (33.5800, -7.6400, "Californie"),
            (33.5200, -7.5800, "Oulfa"),
            (33.6200, -7.6000, "Sidi Bernoussi"),
            (33.5600, -7.5200, "Roches Noires"),
            (33.5900, -7.5400, "Belvédère")
        ]

        phones = [
            "0661234567", "0662345678", "0663456789", "0664567890", "0665678901",
            "0666789012", "0667890123", "0668901234", "0669012345", "0660123456"
        ]

        # Get available items
        items = list(Item.objects.all())
        if not items:
            self.stdout.write(self.style.ERROR('No items found. Run seed_catalog first.'))
            return

        created_orders = 0

        for i, ((lat, lng, area), phone) in enumerate(zip(locations, phones)):
            # Add some randomness to coordinates (±0.01 degrees ≈ ±1km)
            random_lat = lat + random.uniform(-0.01, 0.01)
            random_lng = lng + random.uniform(-0.01, 0.01)
            
            # Create order
            order = Order.objects.create(
                customer_phone=phone,
                location_lat=random_lat,
                location_lng=random_lng,
                delivery_price_offer=random.uniform(15.0, 35.0),
                status=Order.Status.PENDING
            )

            # Add 1-3 random items to each order
            num_items = random.randint(1, 3)
            selected_items = random.sample(items, min(num_items, len(items)))
            
            for item in selected_items:
                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=random.randint(1, 3)
                )

            created_orders += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created order #{order.id} for {phone} in {area} '
                    f'({random_lat:.4f}, {random_lng:.4f}) - {order.delivery_price_offer:.2f}€'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_orders} test orders distributed around Casablanca')
        )
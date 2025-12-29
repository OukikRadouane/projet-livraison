from django.core.management.base import BaseCommand
from orders.models import Order
from catalog.models import Item
import random
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create test orders in Marrakech'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of orders to create')

    def handle(self, *args, **options):
        count = options['count']
        
        # Marrakech neighborhoods with GPS coordinates
        marrakech_locations = [
            {"name": "Gueliz", "lat": 31.6295, "lng": -8.0076, "phone": "+212661234567"},
            {"name": "Medina", "lat": 31.6260, "lng": -7.9890, "phone": "+212662345678"},
            {"name": "Hivernage", "lat": 31.6180, "lng": -8.0150, "phone": "+212663456789"},
            {"name": "Majorelle", "lat": 31.6410, "lng": -8.0030, "phone": "+212664567890"},
            {"name": "Agdal", "lat": 31.6050, "lng": -8.0200, "phone": "+212665678901"},
            {"name": "Targa", "lat": 31.6500, "lng": -7.9800, "phone": "+212666789012"},
            {"name": "Semlalia", "lat": 31.6100, "lng": -8.0400, "phone": "+212667890123"},
            {"name": "Daoudiate", "lat": 31.6350, "lng": -7.9700, "phone": "+212668901234"},
            {"name": "M'hamid", "lat": 31.6000, "lng": -8.0100, "phone": "+212669012345"},
            {"name": "Sidi Youssef Ben Ali", "lat": 31.5800, "lng": -8.0300, "phone": "+212660123456"}
        ]
        
        # Get catalog items
        items = list(Item.objects.all())
        if not items:
            self.stdout.write(self.style.ERROR('No catalog items found. Run seed_catalog first.'))
            return
        
        created_orders = []
        
        for i in range(count):
            # Random location in Marrakech
            location = random.choice(marrakech_locations)
            
            # Add small random offset for variety
            lat_offset = random.uniform(-0.01, 0.01)
            lng_offset = random.uniform(-0.01, 0.01)
            
            # Create order
            order = Order.objects.create(
                customer_phone=location["phone"],
                location_lat=location["lat"] + lat_offset,
                location_lng=location["lng"] + lng_offset,
                delivery_price_offer=Decimal(random.uniform(15.0, 45.0)),
                status=Order.Status.PENDING
            )
            
            # Add random items to order
            num_items = random.randint(1, 4)
            selected_items = random.sample(items, min(num_items, len(items)))
            
            for item in selected_items:
                quantity = random.randint(1, 3)
                order.items.create(
                    item=item,
                    quantity=quantity
                )
            
            created_orders.append(order)
            self.stdout.write(f"Created order #{order.id} in {location['name']} - {order.delivery_price_offer}€")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(created_orders)} test orders in Marrakech')
        )
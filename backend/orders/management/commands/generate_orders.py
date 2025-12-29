import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order, OrderItem
from catalog.models import Item


class Command(BaseCommand):
    help = 'Generate virtual orders for clients in Marrakech'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of orders to generate')

    def handle(self, *args, **options):
        count = options['count']
        
        # Marrakech coordinates bounds
        marrakech_bounds = {
            'lat_min': 31.580, 'lat_max': 31.680,
            'lng_min': -8.050, 'lng_max': -7.950
        }
        
        # Phone prefixes for Morocco
        phone_prefixes = ['0661', '0662', '0663', '0664', '0665', '0666', '0667', '0668', '0669']
        
        # Get available items
        items = list(Item.objects.all())
        if not items:
            self.stdout.write(self.style.ERROR('No items found. Run seed_catalog first.'))
            return

        orders_created = 0
        
        for _ in range(count):
            # Generate random location in Marrakech
            lat = random.uniform(marrakech_bounds['lat_min'], marrakech_bounds['lat_max'])
            lng = random.uniform(marrakech_bounds['lng_min'], marrakech_bounds['lng_max'])
            
            # Generate phone number
            phone = random.choice(phone_prefixes) + str(random.randint(100000, 999999))
            
            # Generate delivery price (20-100 MAD)
            delivery_price = Decimal(str(random.randint(20, 100)))
            
            # Create order
            order = Order.objects.create(
                customer_phone=phone,
                location_lat=lat,
                location_lng=lng,
                delivery_price_offer=delivery_price
            )
            
            # Add 1-5 random items to order
            num_items = random.randint(1, 5)
            selected_items = random.sample(items, min(num_items, len(items)))
            
            for item in selected_items:
                quantity = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=quantity
                )
            
            orders_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {orders_created} orders in Marrakech')
        )
from django.conf import settings
from django.db import models
from django.utils import timezone
from catalog.models import Item, Store


class Order(models.Model):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		ASSIGNED = "ASSIGNED", "Assigned"
		PICKED_UP = "PICKED_UP", "Picked Up"
		DELIVERED = "DELIVERED", "Delivered"
		CANCELLED = "CANCELLED", "Cancelled"

	customer_phone = models.CharField(max_length=32)
	location_lat = models.FloatField()
	location_lng = models.FloatField()
	delivery_price_offer = models.DecimalField(max_digits=8, decimal_places=2)

	status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
	courier = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
	)
	delivered_at = models.DateTimeField(null=True, blank=True)

	# optional suggested restaurant/location fields (for later use)
	restaurant_name = models.CharField(max_length=120, blank=True, default="")
	restaurant_lat = models.FloatField(null=True, blank=True)
	restaurant_lng = models.FloatField(null=True, blank=True)

	store = models.ForeignKey(Store, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def estimated_weight_kg(self) -> float:
		return sum([oi.quantity * (oi.item.weight_per_unit_kg or 0.0) for oi in self.items.all()])

	def __str__(self) -> str:
		return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
	item = models.ForeignKey(Item, on_delete=models.PROTECT)
	quantity = models.PositiveIntegerField(default=1)

	def __str__(self) -> str:
		return f"{self.quantity} x {self.item.name}"


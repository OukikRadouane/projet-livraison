from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"status",
		"customer_phone",
		"courier",
		"delivery_price_offer",
		"created_at",
	)
	list_filter = ("status",)
	search_fields = ("customer_phone",)
	inlines = [OrderItemInline]


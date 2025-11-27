from django.contrib import admin
from .models import Item, Store


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
	list_display = ("name", "category", "unit", "weight_per_unit_kg")
	search_fields = ("name",)
	list_filter = ("category",)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "location_lat", "location_lng")
    search_fields = ("name",)

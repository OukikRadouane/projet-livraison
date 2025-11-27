from django.contrib import admin
from .models import Store, OptimizedRoute, RouteStop


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'created_at']
    search_fields = ['name', 'address']
    list_filter = ['created_at']


@admin.register(OptimizedRoute)
class OptimizedRouteAdmin(admin.ModelAdmin):
    list_display = ['id', 'courier', 'total_distance', 'total_profit', 'is_active', 'created_at']
    search_fields = ['courier__username']
    list_filter = ['is_active', 'created_at']
    readonly_fields = ['total_distance', 'total_time', 'total_profit', 'delivery_order', 'created_at']


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['sequence', 'stop_type', 'route', 'distance_from_previous', 'estimated_arrival_time']
    search_fields = ['route__id']
    list_filter = ['stop_type', 'estimated_arrival_time']
    readonly_fields = ['estimated_arrival_time']

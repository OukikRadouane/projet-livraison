from django.db import models
from django.conf import settings
from orders.models import Order


class Store(models.Model):
    """Magasins (Bim, Marjan, Aswa9 Salam, etc.)"""
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=500)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Stores"

    def __str__(self):
        return self.name


class OptimizedRoute(models.Model):
    """Route optimisée pour le livreur"""
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='optimized_routes')
    total_distance = models.FloatField()  # km
    total_time = models.FloatField()  # minutes
    total_profit = models.FloatField()  # prix offerts
    delivery_order = models.JSONField()  # [{"type": "store"/"client", "id": ..., "order": 1}, ...]
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Route {self.id} - {self.courier.username}"


class RouteStop(models.Model):
    """Arrêt individual dans une route"""
    STOP_TYPE_CHOICES = [
        ('store', 'Magasin'),
        ('client', 'Client'),
        ('depot', 'Dépôt'),
    ]
    
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE, related_name='stops')
    stop_type = models.CharField(max_length=10, choices=STOP_TYPE_CHOICES)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    sequence = models.IntegerField()  # Ordre de visite
    latitude = models.FloatField()
    longitude = models.FloatField()
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    distance_from_previous = models.FloatField(default=0)  # km

    class Meta:
        ordering = ['route', 'sequence']

    def __str__(self):
        return f"{self.get_stop_type_display()} #{self.sequence} - Route {self.route.id}"

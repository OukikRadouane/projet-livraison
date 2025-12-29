from django.db import models
from django.conf import settings
from orders.models import Order

class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_PICKED_UP = "ORDER_PICKED_UP", "Commande ramassée"
        ORDER_DELIVERED = "ORDER_DELIVERED", "Commande livrée"
    
    phone = models.CharField(max_length=32)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type} - {self.phone}"

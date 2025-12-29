from django.urls import path
from .views import CustomerNotificationsView

urlpatterns = [
    path('customer/', CustomerNotificationsView.as_view(), name='customer-notifications'),
]
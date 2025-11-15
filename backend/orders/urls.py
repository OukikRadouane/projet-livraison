from django.urls import path
from .views import (
    AcceptOrderView,
    CourierActiveOrdersView,
    CourierCompletedOrdersView,
    CourierCancelOrderView,
    OrderCreateView,
    PendingOrdersListView,
    UpdateOrderStatusView,
)

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("pending/", PendingOrdersListView.as_view(), name="orders-pending"),
    path("courier/active/", CourierActiveOrdersView.as_view(), name="orders-active"),
    path("courier/completed/", CourierCompletedOrdersView.as_view(), name="orders-completed"),
    path("<int:pk>/accept/", AcceptOrderView.as_view(), name="order-accept"),
    path("<int:pk>/cancel/", CourierCancelOrderView.as_view(), name="order-cancel"),
    path("<int:pk>/status/", UpdateOrderStatusView.as_view(), name="order-status"),
]

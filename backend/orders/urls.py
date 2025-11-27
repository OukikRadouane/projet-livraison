from django.urls import path
from .views import (
    AcceptOrderView,
    CourierActiveOrdersView,
    CourierCompletedOrdersView,
    CourierDeleteCompletedAllView,
    CourierDeleteCompletedByDateView,
    CourierDeleteCompletedOneView,
    CourierCancelOrderView,
    OrderCreateView,
    OrderDetailView,
    PendingOrdersListView,
    UpdateOrderStatusView,
    OptimizeRouteView,
)

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("pending/", PendingOrdersListView.as_view(), name="orders-pending"),
    path("courier/active/", CourierActiveOrdersView.as_view(), name="orders-active"),
    path("courier/completed/", CourierCompletedOrdersView.as_view(), name="orders-completed"),
    path("courier/completed/delete/all/", CourierDeleteCompletedAllView.as_view(), name="orders-completed-delete-all"),
    path("courier/completed/delete/<int:pk>/", CourierDeleteCompletedOneView.as_view(), name="orders-completed-delete-one"),
    path("courier/completed/delete/by-date/", CourierDeleteCompletedByDateView.as_view(), name="orders-completed-delete-by-date"),
    path("<int:pk>/accept/", AcceptOrderView.as_view(), name="order-accept"),
    path("<int:pk>/cancel/", CourierCancelOrderView.as_view(), name="order-cancel"),
    path("<int:pk>/status/", UpdateOrderStatusView.as_view(), name="order-status"),
    path("optimize/", OptimizeRouteView.as_view(), name="optimize-route"),
]

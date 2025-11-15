from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderListSerializer, OrderSerializer


class OrderCreateView(generics.CreateAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer
	permission_classes = [permissions.AllowAny]


class PendingOrdersListView(generics.ListAPIView):
	serializer_class = OrderListSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Order.objects.none()
		return Order.objects.filter(status=Order.Status.PENDING).order_by("-created_at")


class CourierActiveOrdersView(generics.ListAPIView):
	serializer_class = OrderListSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Order.objects.none()
		return (
			Order.objects.filter(
				courier=user,
				status__in=[Order.Status.ASSIGNED, Order.Status.PICKED_UP],
			)
			.order_by("-created_at")
		)


class CourierCompletedOrdersView(generics.ListAPIView):
	serializer_class = OrderListSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Order.objects.none()
		return (
			Order.objects.filter(courier=user, status=Order.Status.DELIVERED)
			.order_by("-delivered_at", "-created_at")
		)


class AcceptOrderView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, pk: int):
		user = request.user
		order = get_object_or_404(Order, pk=pk)
		if order.status != Order.Status.PENDING:
			return Response({"detail": "Order not pending."}, status=status.HTTP_400_BAD_REQUEST)
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can accept orders."}, status=status.HTTP_403_FORBIDDEN)
		order_weight = order.estimated_weight_kg()
		if order_weight > user.capacity_kg:
			return Response(
				{"detail": "Le poids de la commande dépasse votre capacité maximale."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		active_orders = Order.objects.filter(
			courier=user,
			status__in=[Order.Status.ASSIGNED, Order.Status.PICKED_UP],
		)
		current_weight = sum(o.estimated_weight_kg() for o in active_orders)
		if current_weight + order_weight > user.capacity_kg:
			return Response(
				{
					"detail": (
						"Accepter cette commande dépasserait votre capacité totale autorisée."
					)
				},
				status=status.HTTP_400_BAD_REQUEST,
			)
		order.courier = user
		order.status = Order.Status.ASSIGNED
		order.delivered_at = None
		order.save(update_fields=["courier", "status", "delivered_at"])
		return Response(OrderListSerializer(order).data)


class UpdateOrderStatusView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def patch(self, request, pk: int):
		order = get_object_or_404(Order, pk=pk)
		status_value = request.data.get("status")
		allowed = {Order.Status.DELIVERED, Order.Status.PICKED_UP}
		user = request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can update order status."}, status=status.HTTP_403_FORBIDDEN)
		if order.courier_id != user.id:
			return Response({"detail": "Cette commande n'est pas associée à votre compte."}, status=status.HTTP_403_FORBIDDEN)
		if status_value not in allowed:
			return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
		order.status = status_value
		if status_value == Order.Status.DELIVERED:
			order.delivered_at = timezone.now()
		else:
			order.delivered_at = None
		order.save(update_fields=["status", "delivered_at"])
		return Response(OrderListSerializer(order).data)


class CourierCancelOrderView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, pk: int):
		user = request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can cancel assignments."}, status=status.HTTP_403_FORBIDDEN)
		order = get_object_or_404(Order, pk=pk)
		if order.courier_id != user.id:
			return Response({"detail": "Cette commande n'est pas associée à votre compte."}, status=status.HTTP_403_FORBIDDEN)
		if order.status not in {Order.Status.ASSIGNED, Order.Status.PICKED_UP}:
			return Response({"detail": "Impossible d'annuler cette commande."}, status=status.HTTP_400_BAD_REQUEST)
		order.courier = None
		order.status = Order.Status.PENDING
		order.delivered_at = None
		order.save(update_fields=["courier", "status", "delivered_at"])
		return Response(OrderListSerializer(order).data)


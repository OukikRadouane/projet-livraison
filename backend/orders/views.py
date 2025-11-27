from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime

from .models import Order
from .serializers import OrderListSerializer, OrderSerializer, OrderDetailSerializer
from .optimization import knapsack_branch_and_bound, tsp_nearest_neighbor


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


class CourierDeleteCompletedAllView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def delete(self, request):
		user = request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can manage history."}, status=status.HTTP_403_FORBIDDEN)
		qs = Order.objects.filter(courier=user, status=Order.Status.DELIVERED)
		count = qs.count()
		qs.delete()
		return Response({"deleted": count})


class CourierDeleteCompletedOneView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def delete(self, request, pk: int):
		user = request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can manage history."}, status=status.HTTP_403_FORBIDDEN)
		order = get_object_or_404(Order, pk=pk)
		if order.courier_id != user.id or order.status != Order.Status.DELIVERED:
			return Response({"detail": "Not a delivered order of this courier."}, status=status.HTTP_400_BAD_REQUEST)
		order.delete()
		return Response({"deleted": 1})


class CourierDeleteCompletedByDateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def delete(self, request):
		user = request.user
		if not hasattr(user, "role") or user.role != "COURIER":
			return Response({"detail": "Only couriers can manage history."}, status=status.HTTP_403_FORBIDDEN)
		date_str = request.query_params.get("date") or request.data.get("date")
		if not date_str:
			return Response({"detail": "Missing date (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)
		try:
			day = datetime.strptime(date_str, "%Y-%m-%d").date()
		except ValueError:
			return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
		start = datetime.combine(day, datetime.min.time())
		end = datetime.combine(day, datetime.max.time())
		qs = Order.objects.filter(
			courier=user,
			status=Order.Status.DELIVERED,
			delivered_at__gte=start,
			delivered_at__lte=end,
		)
		count = qs.count()
		qs.delete()
		return Response({"deleted": count, "date": date_str})


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


class OrderDetailView(generics.RetrieveAPIView):
		queryset = Order.objects.all()
		serializer_class = OrderDetailSerializer
		permission_classes = [permissions.IsAuthenticated]

class OptimizeRouteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.role == 'COURIER':
            return Response({"detail": "Seuls les livreurs peuvent optimiser les trajets."}, status=status.HTTP_403_FORBIDDEN)
        
        if user.location_lat is None or user.location_lng is None:
            return Response({"detail": "La localisation du livreur n'est pas définie."}, status=status.HTTP_400_BAD_REQUEST)
        
        courier_location = (user.location_lat, user.location_lng)
        
        # Récupérer les commandes pendantes
        pending_orders = Order.objects.filter(status=Order.Status.PENDING)
        
        # Sélectionner les commandes optimales avec Knapsack
        selected_orders = knapsack_branch_and_bound(user.capacity_kg, list(pending_orders))
        
        # Calculer le chemin optimal avec TSP
        optimal_path = tsp_nearest_neighbor(courier_location, selected_orders)
        
        return Response({
            "selected_orders": OrderListSerializer(selected_orders, many=True).data,
            "optimal_path": optimal_path
        })


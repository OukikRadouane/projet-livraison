from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime

from .models import Order
from .serializers import OrderListSerializer, OrderSerializer, OrderDetailSerializer
from logistics.optimizer import order_distance_km, knapsack_max_profit, nearest_neighbor_route
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class OrderCreateView(generics.CreateAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	def create(self, request, *args, **kwargs):
		user = getattr(request, "user", None)
		data = request.data.copy()
		# If authenticated and phone missing, default from profile
		if getattr(user, "is_authenticated", False):
			if not data.get("customer_phone") and getattr(user, "phone", ""):
				data["customer_phone"] = user.phone
		serializer = self.get_serializer(data=data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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



class CourierOptimizeView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, *args, **kwargs):
		# Expect body: { "courier": {"lat": float, "lng": float}, "capacity_km": float }
		# Uses current user's pending orders as candidates
		data = request.data or {}
		courier_lat = data.get("courier", {}).get("lat")
		courier_lng = data.get("courier", {}).get("lng")
		capacity_km = float(data.get("capacity_km", 10.0))
		if courier_lat is None or courier_lng is None:
			return Response({"detail": "courier.lat and courier.lng are required"}, status=status.HTTP_400_BAD_REQUEST)

		courier_pos = (float(courier_lat), float(courier_lng))

		# Candidate orders: pending and nearby/available; here we use all pending
		candidates = Order.objects.filter(status=Order.Status.PENDING)
		items = []
		points = []
		for o in candidates:
			customer = (o.location_lat, o.location_lng)
			restaurant = (o.restaurant_lat, o.restaurant_lng) if o.restaurant_lat is not None and o.restaurant_lng is not None else None
			dist_km = order_distance_km(courier_pos, customer, restaurant)
			profit = float(o.delivery_price_offer)
			items.append({"id": o.id, "profit": profit, "distance_km": dist_km, "customer": customer})
			points.append(customer)

		selected = knapsack_max_profit(items, capacity_km)
		# Build route via nearest neighbor from courier to customers of selected orders
		selected_points = [item["customer"] for item in selected]
		route_order_indices = nearest_neighbor_route(courier_pos, selected_points) if selected_points else []
		ordered_ids = [selected[idx]["id"] for idx in route_order_indices] if route_order_indices else [i["id"] for i in selected]

		total_profit = sum(i["profit"] for i in selected)
		total_distance = sum(i["distance_km"] for i in selected)

		return Response({
			"selected_order_ids": ordered_ids,
			"total_profit": total_profit,
			"total_distance_km": total_distance,
			"capacity_km": capacity_km,
			"count": len(selected),
		})


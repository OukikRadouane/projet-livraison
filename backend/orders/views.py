from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime

from .models import Order
from .serializers import OrderListSerializer, OrderSerializer, OrderDetailSerializer
from logistics.advanced_optimizer import AdvancedDeliveryOptimizer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notifications.models import Notification


class CustomerOrdersView(generics.ListAPIView):
	serializer_class = OrderDetailSerializer
	permission_classes = [permissions.AllowAny]

	def get_queryset(self):
		phone = self.request.query_params.get('phone')
		if not phone:
			return Order.objects.none()
		return Order.objects.filter(customer_phone=phone).order_by('-created_at')


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
		
		# Store previous status for optimization trigger
		previous_status = order.status
		
		order.status = status_value
		if status_value == Order.Status.DELIVERED:
			order.delivered_at = timezone.now()
		else:
			order.delivered_at = None
		order.save(update_fields=["status", "delivered_at"])
		
		# Send notification to customer when order is picked up
		if status_value == Order.Status.PICKED_UP and previous_status != Order.Status.PICKED_UP:
			Notification.objects.create(
				phone=order.customer_phone,
				order=order,
				type=Notification.Type.ORDER_PICKED_UP,
				message=f"Votre commande #{order.id} a été ramassée par le livreur et est en route."
			)
		
		# Auto-trigger optimization when order is delivered
		if status_value == Order.Status.DELIVERED and previous_status != Order.Status.DELIVERED:
			self._trigger_auto_optimization(user)
		
		return Response(OrderListSerializer(order).data)
	
	def _trigger_auto_optimization(self, courier):
		"""Auto-trigger optimization after delivery completion"""
		try:
			# Get courier's remaining active orders
			active_orders = Order.objects.filter(
				courier=courier,
				status__in=[Order.Status.ASSIGNED, Order.Status.PICKED_UP]
			)
			
			# If courier has remaining capacity, suggest new orders
			if active_orders.count() < 3:  # Max 3 orders simultaneously
				current_weight = sum(o.estimated_weight_kg() for o in active_orders)
				remaining_capacity = courier.capacity_kg - current_weight
				
				if remaining_capacity > 1.0:  # At least 1kg remaining
					# Get pending orders that fit remaining capacity
					pending_orders = Order.objects.filter(
						status=Order.Status.PENDING
					).exclude(
						total_weight_kg__gt=remaining_capacity
					)[:5]  # Limit to 5 candidates
					
					# Simple auto-assignment of best profit/weight ratio
					if pending_orders.exists():
						best_order = max(pending_orders, 
							key=lambda o: float(o.delivery_price_offer) / max(o.estimated_weight_kg(), 0.1))
						
						# Auto-assign if profitable
						if float(best_order.delivery_price_offer) > 10.0:  # Min 10€ profit
							best_order.courier = courier
							best_order.status = Order.Status.ASSIGNED
							best_order.save(update_fields=["courier", "status"])
		except Exception:
			pass  # Silent fail for auto-optimization


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
		data = request.data or {}
		courier_data = data.get("courier", {})
		courier_lat = courier_data.get("lat")
		courier_lng = courier_data.get("lng")
		capacity_km = float(data.get("capacity_km", 10.0))
		
		if courier_lat is None or courier_lng is None:
			return Response({"detail": "courier.lat and courier.lng are required"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			courier_pos = (float(courier_lat), float(courier_lng))
			# Validate GPS coordinates
			if not (-90 <= courier_pos[0] <= 90) or not (-180 <= courier_pos[1] <= 180):
				return Response({"detail": "Invalid GPS coordinates"}, status=status.HTTP_400_BAD_REQUEST)
		except (ValueError, TypeError):
			return Response({"detail": "Invalid courier coordinates"}, status=status.HTTP_400_BAD_REQUEST)

		# Get pending orders AND active orders for this courier
		candidates = Order.objects.filter(status=Order.Status.PENDING)
		active_orders = Order.objects.filter(
			courier=request.user,
			status__in=[Order.Status.ASSIGNED, Order.Status.PICKED_UP]
		)
		
		orders_data = []
		
		print(f"DEBUG: Found {candidates.count()} pending + {active_orders.count()} active orders")
		
		# Add pending orders
		for order in candidates:
			order_data = {
				"id": order.id,
				"location_lat": order.location_lat,
				"location_lng": order.location_lng,
				"total_weight_kg": order.estimated_weight_kg(),
				"delivery_price_offer": str(order.delivery_price_offer),
				"customer_phone": order.customer_phone,
				"status": "PENDING"
			}
			orders_data.append(order_data)
			print(f"DEBUG: Pending Order {order.id}")
		
		# Add active orders (already accepted)
		for order in active_orders:
			order_data = {
				"id": order.id,
				"location_lat": order.location_lat,
				"location_lng": order.location_lng,
				"total_weight_kg": order.estimated_weight_kg(),
				"delivery_price_offer": str(order.delivery_price_offer),
				"customer_phone": order.customer_phone,
				"status": order.status
			}
			orders_data.append(order_data)
			print(f"DEBUG: Active Order {order.id} - Status: {order.status}")

		# Use realistic optimizer instead of advanced optimizer
		from logistics.realistic_optimizer import RealisticDeliveryOptimizer
		optimizer = RealisticDeliveryOptimizer()
		result = optimizer.optimize_realistic_route(
			courier_pos=courier_pos,
			orders_data=orders_data
		)

		return Response({
			"selected_order_ids": result["selected_order_ids"],
			"total_profit": result["total_profit"],
			"total_distance_km": result["total_distance"],
			"total_weight_kg": result["total_weight"],
			"estimated_duration_min": result["estimated_duration_min"],
			"capacity_km": capacity_km,
			"count": len(result["selected_order_ids"]),
			"route_details": result.get("route_details", []),
			"full_route_coordinates": result.get("full_route_coordinates", []),
			"algorithm": "Realistic Delivery Optimizer"
		})


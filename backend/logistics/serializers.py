from rest_framework import serializers
from .models import Store, OptimizedRoute, RouteStop
from orders.serializers import OrderSerializer


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'latitude', 'longitude', 'address', 'phone', 'created_at']


class RouteStopSerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source='order', read_only=True)
    store_details = StoreSerializer(source='store', read_only=True)
    
    class Meta:
        model = RouteStop
        fields = [
            'id', 'route', 'stop_type', 'store', 'store_details',
            'order', 'order_details', 'sequence', 'latitude', 'longitude',
            'estimated_arrival_time', 'distance_from_previous'
        ]


class OptimizedRouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    courier_name = serializers.CharField(source='courier.username', read_only=True)
    
    class Meta:
        model = OptimizedRoute
        fields = [
            'id', 'courier', 'courier_name', 'total_distance', 'total_time',
            'total_profit', 'delivery_order', 'is_active', 'created_at', 'stops'
        ]

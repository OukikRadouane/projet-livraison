from rest_framework import serializers
from .models import Order, OrderItem
from catalog.models import Item


class OrderItemCreateSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), write_only=True, source="item"
    )

    class Meta:
        model = OrderItem
        fields = ["item_id", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_phone",
            "location_lat",
            "location_lng",
            "delivery_price_offer",
            "status",
            "courier",
            "restaurant_name",
            "restaurant_lat",
            "restaurant_lng",
            "items",
            "created_at",
        ]
        read_only_fields = ["status", "courier", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class OrderListSerializer(serializers.ModelSerializer):
    total_weight_kg = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "delivered_at",
            "customer_phone",
            "location_lat",
            "location_lng",
            "delivery_price_offer",
            "courier",
            "total_weight_kg",
            "created_at",
        ]

    def get_total_weight_kg(self, obj):
        return obj.estimated_weight_kg()

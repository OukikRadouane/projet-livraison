from rest_framework import generics, permissions
from .models import Item
from .serializers import ItemSerializer


class ItemListView(generics.ListAPIView):
	queryset = Item.objects.all().order_by("name")
	serializer_class = ItemSerializer
	permission_classes = [permissions.AllowAny]

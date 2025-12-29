from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class CustomerNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        phone = self.request.query_params.get('phone')
        if not phone:
            return Notification.objects.none()
        return Notification.objects.filter(phone=phone).order_by('-sent_at')
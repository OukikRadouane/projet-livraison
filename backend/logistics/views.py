from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Store, OptimizedRoute, RouteStop
from .serializers import StoreSerializer, OptimizedRouteSerializer, RouteStopSerializer
from .services import RouteOptimizationService
from orders.models import Order


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste tous les magasins"""
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]


class OptimizedRouteViewSet(viewsets.ModelViewSet):
    """Gère les routes optimisées"""
    queryset = OptimizedRoute.objects.all()
    serializer_class = OptimizedRouteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Les livreurs voient seulement leurs routes"""
        user = self.request.user
        if user.is_courier():
            return OptimizedRoute.objects.filter(courier=user)
        return OptimizedRoute.objects.all()
    
    @action(detail=False, methods=['post'])
    def calculate_route(self, request):
        """
        POST /api/optimized-routes/calculate_route/
        Calcule la route optimale pour le livreur courant
        """
        try:
            optimized_route = RouteOptimizationService.calculate_optimal_route(
                request.user.id
            )
            serializer = self.get_serializer(optimized_route)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur serveur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail='pk', methods=['post'])
    def activate_route(self, request, pk=None):
        """
        POST /api/optimized-routes/{id}/activate_route/
        Active une route calculée et assigne les commandes au livreur
        """
        route = self.get_object()
        
        if route.is_active:
            return Response(
                {"error": "Cette route est déjà active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que c'est bien le livreur qui active sa route
        if route.courier != request.user:
            return Response(
                {"error": "Vous ne pouvez pas activer la route d'un autre livreur"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        route.is_active = True
        route.save()
        
        # Assigner les commandes au livreur
        for stop in route.stops.filter(stop_type='client'):
            if stop.order:
                stop.order.courier = request.user
                stop.order.status = Order.Status.ASSIGNED
                stop.order.save()
        
        serializer = self.get_serializer(route)
        return Response(
            {
                "status": "Route activée",
                "route": serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail='pk', methods=['post'])
    def deactivate_route(self, request, pk=None):
        """Désactive une route et réinitialise les commandes"""
        route = self.get_object()
        
        if not route.is_active:
            return Response(
                {"error": "Cette route n'est pas active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que c'est bien le livreur qui désactive sa route
        if route.courier != request.user:
            return Response(
                {"error": "Vous ne pouvez pas désactiver la route d'un autre livreur"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        route.is_active = False
        route.save()
        
        # Réassigner les commandes à PENDING
        for stop in route.stops.filter(stop_type='client'):
            if stop.order and stop.order.status != Order.Status.DELIVERED:
                stop.order.courier = None
                stop.order.status = Order.Status.PENDING
                stop.order.save()
        
        serializer = self.get_serializer(route)
        return Response(
            {
                "status": "Route désactivée",
                "route": serializer.data
            },
            status=status.HTTP_200_OK
        )


class RouteStopViewSet(viewsets.ReadOnlyModelViewSet):
    """Affiche les arrêts d'une route"""
    queryset = RouteStop.objects.all()
    serializer_class = RouteStopSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Les livreurs voient seulement les arrêts de leurs routes"""
        user = self.request.user
        if user.is_courier():
            return RouteStop.objects.filter(route__courier=user)
        return RouteStop.objects.all()

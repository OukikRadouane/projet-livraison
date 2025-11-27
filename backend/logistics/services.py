import math
from typing import List, Dict, Tuple
import requests
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Store, OptimizedRoute, RouteStop
from orders.models import Order


class DistanceCalculator:
    """Calcule distances réelles via OSRM"""
    OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
    
    @staticmethod
    def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
        """
        Retourne (distance_km, time_minutes)
        """
        try:
            url = f"{DistanceCalculator.OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
            params = {"overview": "false"}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['routes']:
                    distance_km = data['routes'][0]['distance'] / 1000
                    time_min = data['routes'][0]['duration'] / 60
                    return distance_km, time_min
        except:
            pass
        
        # Fallback : distance euclidienne
        dist = DistanceCalculator.haversine(lat1, lon1, lat2, lon2)
        return dist, dist * 1.5  # estimation temps

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Distance euclidienne en km"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class ClusteringService:
    """Regroupe les clients par proximité"""
    
    @staticmethod
    def cluster_clients(orders: List[Order], max_distance_km: float = 3.0) -> List[List[Order]]:
        """
        Groupe les commandes par proximité (clustering géographique simple)
        """
        if not orders:
            return []
        
        clusters = []
        used = set()
        
        for i, order1 in enumerate(orders):
            if i in used:
                continue
            
            cluster = [order1]
            used.add(i)
            
            for j, order2 in enumerate(orders[i+1:], start=i+1):
                if j in used:
                    continue
                
                dist, _ = DistanceCalculator.get_distance(
                    order1.location_lat,
                    order1.location_lng,
                    order2.location_lat,
                    order2.location_lng
                )
                
                if dist <= max_distance_km:
                    cluster.append(order2)
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters


class StoreSelectionService:
    """Sélectionne les magasins optimaux pour chaque cluster"""
    
    @staticmethod
    def find_optimal_stores(client_cluster: List[Order]) -> List[Store]:
        """
        Trouve les magasins les plus proches du cluster
        """
        if not client_cluster:
            return []
        
        # Centre du cluster (moyenne des coordonnées)
        avg_lat = sum(o.location_lat for o in client_cluster) / len(client_cluster)
        avg_lon = sum(o.location_lng for o in client_cluster) / len(client_cluster)
        
        stores = Store.objects.all()
        store_distances = []
        
        for store in stores:
            dist, _ = DistanceCalculator.get_distance(avg_lat, avg_lon, store.latitude, store.longitude)
            store_distances.append((store, dist))
        
        # Trier par distance et retourner les 3 plus proches
        store_distances.sort(key=lambda x: x[1])
        return [store for store, _ in store_distances[:3]]


class TSPSolver:
    """Résoud le problème du voyageur de commerce"""
    
    @staticmethod
    def solve_tsp(locations: List[Dict]) -> List[int]:
        """
        TSP avec nearest neighbor (heuristique rapide)
        locations = [{"id": 1, "lat": 48.5, "lon": 2.5, "type": "store"}, ...]
        Retourne l'ordre optimal des indices
        """
        if len(locations) <= 2:
            return list(range(len(locations)))
        
        # Nearest Neighbor heuristique
        unvisited = set(range(1, len(locations)))
        current = 0
        route = [0]
        
        while unvisited:
            nearest = min(
                unvisited,
                key=lambda i: DistanceCalculator.get_distance(
                    locations[current]['lat'],
                    locations[current]['lon'],
                    locations[i]['lat'],
                    locations[i]['lon']
                )[0]
            )
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route


class KnapsackSolver:
    """Branch & Bound pour le problème du sac à dos (capacité 10kg)"""
    
    MAX_CAPACITY = 10000  # 10kg en grammes
    
    @staticmethod
    def solve_knapsack(items: List[Dict]) -> Dict:
        """
        Branch & Bound pour optimiser les items à livrer
        items = [{"id": 1, "weight": 500, "value": 100}, ...]
        Retourne {"selected": [item_ids], "total_weight": ..., "total_value": ...}
        """
        n = len(items)
        best_value = 0
        best_items = []
        
        def bound(i, current_weight, current_value):
            """Calcule la borne supérieure"""
            if current_weight >= KnapsackSolver.MAX_CAPACITY:
                return current_value
            
            remaining_capacity = KnapsackSolver.MAX_CAPACITY - current_weight
            remaining_value = current_value
            
            for j in range(i, n):
                if items[j]['weight'] <= remaining_capacity:
                    remaining_capacity -= items[j]['weight']
                    remaining_value += items[j]['value']
            
            return remaining_value
        
        def backtrack(i, current_weight, current_value, selected):
            nonlocal best_value, best_items
            
            if i == n:
                if current_value > best_value:
                    best_value = current_value
                    best_items = selected.copy()
                return
            
            # Pruning
            if bound(i, current_weight, current_value) <= best_value:
                return
            
            # Inclure l'item
            if current_weight + items[i]['weight'] <= KnapsackSolver.MAX_CAPACITY:
                selected.append(items[i]['id'])
                backtrack(i + 1, current_weight + items[i]['weight'],
                         current_value + items[i]['value'], selected)
                selected.pop()
            
            # Exclure l'item
            backtrack(i + 1, current_weight, current_value, selected)
        
        backtrack(0, 0, 0, [])
        
        total_weight = sum(
            item['weight'] for item in items if item['id'] in best_items
        )
        
        return {
            "selected": best_items,
            "total_weight": total_weight,
            "total_value": best_value
        }


class RouteOptimizationService:
    """Service principal d'optimisation"""
    
    @staticmethod
    def calculate_optimal_route(courier_id: int) -> OptimizedRoute:
        """
        Calcule la route optimale pour le livreur
        Flux : Clustering → Sélection magasins → TSP magasins → TSP clients
        """
        from accounts.models import User
        
        courier = User.objects.get(id=courier_id)
        
        # 1. Récupérer les commandes non affectées
        pending_orders = list(Order.objects.filter(
            status=Order.Status.PENDING,
            courier__isnull=True
        ))
        
        if not pending_orders:
            raise ValueError("Aucune commande disponible")
        
        # 2. Clustering des clients
        clusters = ClusteringService.cluster_clients(pending_orders)
        
        # 3. Sélectionner magasins et construire liste complète de points
        all_stops = []
        
        # Ajouter démarrage (localisation courrier ou centre-ville par défaut)
        all_stops.append({
            "id": "depot",
            "type": "depot",
            "lat": 33.5731,
            "lon": -7.5898,
        })
        
        selected_orders = []
        
        for cluster in clusters:
            stores = StoreSelectionService.find_optimal_stores(cluster)
            
            for store in stores:
                all_stops.append({
                    "id": f"store_{store.id}",
                    "type": "store",
                    "lat": store.latitude,
                    "lon": store.longitude,
                    "store_id": store.id,
                })
            
            for order in cluster:
                all_stops.append({
                    "id": f"order_{order.id}",
                    "type": "client",
                    "lat": order.location_lat,
                    "lon": order.location_lng,
                    "order_id": order.id,
                })
                selected_orders.append(order)
        
        # 4. Résoudre TSP
        route_indices = TSPSolver.solve_tsp(all_stops)
        
        # 5. Calculer distance et temps totaux
        total_distance = 0
        total_time = 0
        ordered_stops = []
        
        for i in range(len(route_indices) - 1):
            idx_current = route_indices[i]
            idx_next = route_indices[i + 1]
            
            stop_current = all_stops[idx_current]
            stop_next = all_stops[idx_next]
            
            dist, time = DistanceCalculator.get_distance(
                stop_current['lat'], stop_current['lon'],
                stop_next['lat'], stop_next['lon']
            )
            total_distance += dist
            total_time += time
            
            ordered_stops.append({
                'sequence': i,
                'stop': stop_current,
                'distance_to_next': dist,
                'time_to_next': time
            })
        
        # Ajouter le dernier arrêt
        last_idx = route_indices[-1]
        ordered_stops.append({
            'sequence': len(route_indices) - 1,
            'stop': all_stops[last_idx],
            'distance_to_next': 0,
            'time_to_next': 0
        })
        
        # 6. Créer la route optimisée
        total_profit = sum(o.delivery_price_offer for o in selected_orders)
        
        optimized_route = OptimizedRoute.objects.create(
            courier=courier,
            total_distance=round(total_distance, 2),
            total_time=round(total_time, 2),
            total_profit=float(total_profit),
            delivery_order=[stop['stop'] for stop in ordered_stops],
            is_active=False
        )
        
        # 7. Créer les stops
        current_time = timezone.now()
        
        for stop_data in ordered_stops:
            stop = stop_data['stop']
            seq = stop_data['sequence'] + 1
            
            # Estimer l'heure d'arrivée
            estimated_arrival = current_time + timedelta(minutes=stop_data['time_to_next'])
            
            route_stop = RouteStop.objects.create(
                route=optimized_route,
                stop_type=stop['type'],
                store_id=stop.get('store_id'),
                order_id=stop.get('order_id'),
                sequence=seq,
                latitude=stop['lat'],
                longitude=stop['lon'],
                estimated_arrival_time=estimated_arrival,
                distance_from_previous=round(stop_data['distance_to_next'], 2)
            )
        
        return optimized_route

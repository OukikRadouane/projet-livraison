"""
Optimiseur logistique réaliste pour système de livraison
"""
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Store:
    id: int
    name: str
    lat: float
    lng: float
    opening_hours: str  # "08:00-20:00"
    preparation_time_min: int  # Temps préparation commande


@dataclass
class DeliveryTask:
    order_id: int
    store: Store
    customer_lat: float
    customer_lng: float
    pickup_time_estimate: datetime
    delivery_time_estimate: datetime
    profit: float
    weight_kg: float


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance entre deux points GPS"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class RealisticDeliveryOptimizer:
    """Optimiseur logistique réaliste"""
    
    def __init__(self):
        self.stores = [
            Store(1, "Marjane Menara", 31.6295, -8.0076, "08:00-22:00", 15),
            Store(2, "BIM Gueliz", 31.6350, -8.0100, "08:00-21:00", 10),
            Store(3, "Carrefour Al Mazar", 31.6180, -8.0150, "09:00-23:00", 20),
            Store(4, "Atacadao Marrakech", 31.6050, -8.0200, "08:00-22:00", 12),
        ]
        self.avg_speed_kmh = 25  # Vitesse moyenne en ville
        self.service_time_min = 5  # Temps service par arrêt
    
    def optimize_realistic_route(self, courier_pos: Tuple[float, float], 
                               orders_data: List[Dict]) -> Dict:
        """Optimisation réaliste avec workflow pickup → delivery"""
        
        print(f"DEBUG: Starting optimization with {len(orders_data)} orders")
        print(f"DEBUG: Courier position: {courier_pos}")
        
        if not orders_data:
            return self._empty_result()
        
        # Debug: Print order data
        for order in orders_data:
            print(f"DEBUG: Order {order['id']} - Profit: {order.get('delivery_price_offer', 0)}, Weight: {order.get('total_weight_kg', 1.0)}")
        
        # 1. Créer les tâches de livraison réalistes
        delivery_tasks = self._create_delivery_tasks(orders_data)
        print(f"DEBUG: Created {len(delivery_tasks)} delivery tasks")
        
        # 2. Filtrer par contraintes réalistes
        feasible_tasks = self._filter_feasible_tasks(courier_pos, delivery_tasks)
        print(f"DEBUG: {len(feasible_tasks)} feasible tasks after filtering")
        
        # 3. Optimiser par profit/temps
        selected_tasks = self._select_optimal_tasks(feasible_tasks)
        print(f"DEBUG: {len(selected_tasks)} tasks selected")
        
        # 4. Générer itinéraire pickup → delivery
        route = self._generate_realistic_route(courier_pos, selected_tasks)
        
        result = {
            "selected_order_ids": [task.order_id for task in selected_tasks],
            "total_profit": sum(task.profit for task in selected_tasks),
            "total_distance": self._calculate_route_distance(route),
            "total_weight": sum(task.weight_kg for task in selected_tasks),
            "estimated_duration_min": self._calculate_route_duration(route),
            "route_details": route,
            "full_route_coordinates": [[step["lat"], step["lng"]] for step in route]
        }
        
        print(f"DEBUG: Final result - {len(result['selected_order_ids'])} orders, {result['total_profit']}€ profit")
        return result
    
    def _create_delivery_tasks(self, orders_data: List[Dict]) -> List[DeliveryTask]:
        """Créer tâches avec magasins assignés"""
        tasks = []
        now = datetime.now()
        
        print(f"DEBUG: Creating tasks for {len(orders_data)} orders")
        
        for order in orders_data:
            print(f"DEBUG: Processing order {order['id']} with profit {order.get('delivery_price_offer', 0)}")
            
            # Convert string price to float
            try:
                profit = float(order.get('delivery_price_offer', '0'))
            except (ValueError, TypeError):
                profit = 0.0
                print(f"DEBUG: Could not convert price '{order.get('delivery_price_offer')}' to float")
            
            # Assigner magasin le plus proche
            best_store = min(self.stores, 
                           key=lambda s: haversine_km(s.lat, s.lng, 
                                                     order["location_lat"], 
                                                     order["location_lng"]))
            
            print(f"DEBUG: Best store for order {order['id']}: {best_store.name}")
            
            # Calculer temps estimés
            pickup_time = now + timedelta(minutes=best_store.preparation_time_min)
            delivery_distance = haversine_km(best_store.lat, best_store.lng,
                                           order["location_lat"], order["location_lng"])
            delivery_time = pickup_time + timedelta(minutes=delivery_distance / self.avg_speed_kmh * 60)
            
            task = DeliveryTask(
                order_id=order["id"],
                store=best_store,
                customer_lat=order["location_lat"],
                customer_lng=order["location_lng"],
                pickup_time_estimate=pickup_time,
                delivery_time_estimate=delivery_time,
                profit=profit,
                weight_kg=order.get("total_weight_kg", 1.0)
            )
            
            # Mark if this order is already accepted
            task.is_accepted = order.get("status") in ["ASSIGNED", "PICKED_UP"]
            
            tasks.append(task)
            print(f"DEBUG: Created task for order {order['id']} with profit {profit}€, accepted: {task.is_accepted}")
        
        return tasks
    
    def _filter_feasible_tasks(self, courier_pos: Tuple[float, float], 
                             tasks: List[DeliveryTask]) -> List[DeliveryTask]:
        """Filtrer tâches réalisables"""
        feasible = []
        max_distance_km = 300  # Augmenté à 300km pour test inter-villes
        max_delivery_time_hours = 8  # Augmenté à 8h
        
        print(f"DEBUG: Filtering {len(tasks)} tasks from courier position {courier_pos}")
        
        for task in tasks:
            # Distance courier → magasin
            courier_to_store = haversine_km(courier_pos[0], courier_pos[1], 
                                          task.store.lat, task.store.lng)
            
            # Distance magasin → client
            store_to_customer = haversine_km(task.store.lat, task.store.lng,
                                           task.customer_lat, task.customer_lng)
            
            total_distance = courier_to_store + store_to_customer
            
            print(f"DEBUG: Order {task.order_id} - Courier→Store: {courier_to_store:.1f}km, Store→Customer: {store_to_customer:.1f}km, Total: {total_distance:.1f}km, Profit: {task.profit}€")
            
            # Filtres très permissifs pour test
            if (total_distance <= max_distance_km and 
                task.delivery_time_estimate <= datetime.now() + timedelta(hours=max_delivery_time_hours) and
                task.profit >= 1.0):  # Réduit à 1€ minimum
                feasible.append(task)
                print(f"DEBUG: Order {task.order_id} ACCEPTED")
            else:
                reasons = []
                if total_distance > max_distance_km:
                    reasons.append(f"Distance {total_distance:.1f}km > {max_distance_km}km")
                if task.profit < 1.0:
                    reasons.append(f"Profit {task.profit}€ < 1€")
                print(f"DEBUG: Order {task.order_id} REJECTED - {', '.join(reasons)}")
        
        print(f"DEBUG: {len(feasible)} feasible tasks found")
        return feasible
    
    def _select_optimal_tasks(self, tasks: List[DeliveryTask]) -> List[DeliveryTask]:
        """Sélection optimale par ratio profit/temps"""
        if not tasks:
            return []
        
        # Séparer les tâches acceptées et en attente
        accepted_tasks = [task for task in tasks if hasattr(task, 'is_accepted') and task.is_accepted]
        pending_tasks = [task for task in tasks if not (hasattr(task, 'is_accepted') and task.is_accepted)]
        
        print(f"DEBUG: {len(accepted_tasks)} accepted tasks, {len(pending_tasks)} pending tasks")
        
        # Toujours inclure les tâches déjà acceptées
        selected = accepted_tasks.copy()
        
        # Calculer la capacité restante
        used_weight = sum(task.weight_kg for task in accepted_tasks)
        max_weight = 10.0
        max_tasks = 3
        
        remaining_weight = max_weight - used_weight
        remaining_slots = max_tasks - len(accepted_tasks)
        
        print(f"DEBUG: Used weight: {used_weight}kg, Remaining: {remaining_weight}kg, Slots: {remaining_slots}")
        
        # Ajouter de nouvelles tâches si possible
        if remaining_slots > 0 and remaining_weight > 0:
            # Trier par ratio profit/temps
            def profit_time_ratio(task):
                duration_hours = (task.delivery_time_estimate - task.pickup_time_estimate).total_seconds() / 3600
                return task.profit / max(duration_hours, 0.5)
            
            sorted_pending = sorted(pending_tasks, key=profit_time_ratio, reverse=True)
            
            for task in sorted_pending:
                if (len(selected) < max_tasks and 
                    used_weight + task.weight_kg <= max_weight):
                    selected.append(task)
                    used_weight += task.weight_kg
                    print(f"DEBUG: Added new task {task.order_id}")
        
        return selected
    
    def _generate_realistic_route(self, courier_pos: Tuple[float, float], 
                                tasks: List[DeliveryTask]) -> List[Dict]:
        """Générer itinéraire réaliste pickup → delivery"""
        route = []
        step = 1
        
        # Point de départ
        route.append({
            "step": step,
            "type": "start",
            "lat": courier_pos[0],
            "lng": courier_pos[1],
            "description": "Départ livreur",
            "estimated_time": datetime.now().strftime("%H:%M")
        })
        step += 1
        
        # Pour chaque tâche: pickup puis delivery
        for task in tasks:
            # Pickup
            route.append({
                "step": step,
                "type": "pickup",
                "lat": task.store.lat,
                "lng": task.store.lng,
                "store_name": task.store.name,
                "order_id": task.order_id,
                "description": f"Récupération #{task.order_id} - {task.store.name}",
                "estimated_time": task.pickup_time_estimate.strftime("%H:%M"),
                "preparation_time_min": task.store.preparation_time_min
            })
            step += 1
            
            # Delivery
            route.append({
                "step": step,
                "type": "delivery",
                "lat": task.customer_lat,
                "lng": task.customer_lng,
                "order_id": task.order_id,
                "profit": task.profit,
                "description": f"Livraison #{task.order_id}",
                "estimated_time": task.delivery_time_estimate.strftime("%H:%M")
            })
            step += 1
        
        return route
    
    def _calculate_route_distance(self, route: List[Dict]) -> float:
        """Distance totale itinéraire"""
        total = 0
        for i in range(len(route) - 1):
            current = route[i]
            next_point = route[i + 1]
            total += haversine_km(current["lat"], current["lng"],
                                next_point["lat"], next_point["lng"])
        return total
    
    def _calculate_route_duration(self, route: List[Dict]) -> int:
        """Durée totale en minutes"""
        if len(route) < 2:
            return 0
        
        distance_km = self._calculate_route_distance(route)
        travel_time_min = (distance_km / self.avg_speed_kmh) * 60
        service_time_min = len([r for r in route if r["type"] in ["pickup", "delivery"]]) * self.service_time_min
        preparation_time_min = sum(r.get("preparation_time_min", 0) for r in route)
        
        return int(travel_time_min + service_time_min + preparation_time_min)
    
    def _empty_result(self) -> Dict:
        """Résultat vide"""
        return {
            "selected_order_ids": [],
            "total_profit": 0,
            "total_distance": 0,
            "total_weight": 0,
            "estimated_duration_min": 0,
            "route_details": [],
            "full_route_coordinates": []
        }
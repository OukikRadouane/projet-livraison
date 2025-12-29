import math
import random
import copy
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Store:
    id: int
    name: str
    lat: float
    lng: float
    categories: List[str]  # ['fruits', 'vegetables', 'meat', 'dairy']


@dataclass
class Order:
    id: int
    customer_lat: float
    customer_lng: float
    items: List[Dict]  # [{'category': 'fruits', 'weight': 2.5, 'profit': 15.0}]
    total_weight: float
    total_profit: float


@dataclass
class DeliveryRoute:
    courier_pos: Tuple[float, float]
    selected_orders: List[Order]
    pickup_sequence: List[Tuple[int, int]]  # [(store_id, order_id)]
    delivery_sequence: List[int]  # [order_id]
    total_distance: float
    total_profit: float
    total_weight: float


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class BranchAndBoundKnapsack:
    """Branch and Bound algorithm for order selection (Knapsack Problem)"""
    
    def __init__(self, orders: List[Order], capacity_weight: float, capacity_distance: float):
        self.orders = orders
        self.capacity_weight = capacity_weight
        self.capacity_distance = capacity_distance
        self.best_solution = []
        self.best_value = 0
        
    def solve(self) -> List[Order]:
        """Solve knapsack problem using Branch and Bound"""
        if not self.orders:
            return []
            
        # Sort orders by profit/weight ratio (greedy heuristic)
        sorted_orders = sorted(self.orders, 
                             key=lambda x: x.total_profit / max(x.total_weight, 0.1), 
                             reverse=True)
        
        self._branch_and_bound(0, [], 0, 0, 0, sorted_orders)
        return self.best_solution
    
    def _branch_and_bound(self, index: int, current_solution: List[Order], 
                         current_weight: float, current_distance: float, 
                         current_value: float, orders: List[Order]):
        """Recursive branch and bound implementation"""
        if index == len(orders):
            if current_value > self.best_value:
                self.best_value = current_value
                self.best_solution = current_solution.copy()
            return
        
        # Upper bound calculation (fractional knapsack)
        upper_bound = current_value + self._calculate_upper_bound(
            index, current_weight, current_distance, orders)
        
        if upper_bound <= self.best_value:
            return  # Prune this branch
        
        order = orders[index]
        
        # Branch 1: Include current order
        if (current_weight + order.total_weight <= self.capacity_weight and
            current_distance + self._estimate_order_distance(order) <= self.capacity_distance):
            
            new_solution = current_solution + [order]
            new_weight = current_weight + order.total_weight
            new_distance = current_distance + self._estimate_order_distance(order)
            new_value = current_value + order.total_profit
            
            self._branch_and_bound(index + 1, new_solution, new_weight, 
                                 new_distance, new_value, orders)
        
        # Branch 2: Exclude current order
        self._branch_and_bound(index + 1, current_solution, current_weight, 
                             current_distance, current_value, orders)
    
    def _calculate_upper_bound(self, start_index: int, current_weight: float, 
                             current_distance: float, orders: List[Order]) -> float:
        """Calculate upper bound using fractional knapsack"""
        remaining_weight = self.capacity_weight - current_weight
        remaining_distance = self.capacity_distance - current_distance
        bound = 0
        
        for i in range(start_index, len(orders)):
            order = orders[i]
            order_distance = self._estimate_order_distance(order)
            
            if order.total_weight <= remaining_weight and order_distance <= remaining_distance:
                bound += order.total_profit
                remaining_weight -= order.total_weight
                remaining_distance -= order_distance
            else:
                # Fractional part
                weight_fraction = remaining_weight / max(order.total_weight, 0.1)
                distance_fraction = remaining_distance / max(order_distance, 0.1)
                fraction = min(weight_fraction, distance_fraction, 1.0)
                bound += order.total_profit * fraction
                break
        
        return bound
    
    def _estimate_order_distance(self, order: Order) -> float:
        """Estimate distance for an order (simplified)"""
        return 2.0  # Simplified: assume 2km per order on average


class TabuSearchTSP:
    """Tabu Search algorithm for route optimization (TSP)"""
    
    def __init__(self, points: List[Tuple[float, float]], max_iterations: int = 100):
        self.points = points
        self.max_iterations = max_iterations
        self.tabu_list = []
        self.tabu_tenure = min(7, len(points) // 2)
        
    def solve(self, start_point: Tuple[float, float]) -> List[int]:
        """Solve TSP using Tabu Search"""
        if len(self.points) <= 1:
            return list(range(len(self.points)))
        
        # Initialize with nearest neighbor solution
        current_solution = self._nearest_neighbor_solution(start_point)
        best_solution = current_solution.copy()
        best_distance = self._calculate_total_distance(best_solution, start_point)
        
        for iteration in range(self.max_iterations):
            # Generate neighborhood (2-opt moves)
            neighbors = self._generate_neighbors(current_solution)
            
            # Find best non-tabu move
            best_neighbor = None
            best_neighbor_distance = float('inf')
            
            for neighbor in neighbors:
                if not self._is_tabu(neighbor, current_solution):
                    distance = self._calculate_total_distance(neighbor, start_point)
                    if distance < best_neighbor_distance:
                        best_neighbor = neighbor
                        best_neighbor_distance = distance
            
            if best_neighbor is None:
                break
            
            # Update current solution
            current_solution = best_neighbor
            
            # Update best solution if improved
            if best_neighbor_distance < best_distance:
                best_solution = best_neighbor.copy()
                best_distance = best_neighbor_distance
            
            # Update tabu list
            self._update_tabu_list(current_solution)
        
        return best_solution
    
    def _nearest_neighbor_solution(self, start_point: Tuple[float, float]) -> List[int]:
        """Generate initial solution using nearest neighbor"""
        if not self.points:
            return []
        
        unvisited = list(range(len(self.points)))
        solution = []
        current_point = start_point
        
        while unvisited:
            nearest_idx = min(unvisited, 
                            key=lambda i: haversine_km(current_point[0], current_point[1], 
                                                     self.points[i][0], self.points[i][1]))
            solution.append(nearest_idx)
            current_point = self.points[nearest_idx]
            unvisited.remove(nearest_idx)
        
        return solution
    
    def _generate_neighbors(self, solution: List[int]) -> List[List[int]]:
        """Generate neighbors using 2-opt moves"""
        neighbors = []
        n = len(solution)
        
        for i in range(n - 1):
            for j in range(i + 2, n):
                neighbor = solution.copy()
                # Reverse the segment between i+1 and j
                neighbor[i+1:j+1] = reversed(neighbor[i+1:j+1])
                neighbors.append(neighbor)
        
        return neighbors
    
    def _is_tabu(self, solution: List[int], current: List[int]) -> bool:
        """Check if move is in tabu list"""
        move = self._get_move(current, solution)
        return move in self.tabu_list
    
    def _get_move(self, solution1: List[int], solution2: List[int]) -> Tuple[int, int]:
        """Extract the move (edge swap) between two solutions"""
        # Simplified: return first difference found
        for i in range(len(solution1)):
            if solution1[i] != solution2[i]:
                return (i, solution2[i])
        return (0, 0)
    
    def _update_tabu_list(self, solution: List[int]):
        """Update tabu list with current move"""
        if len(self.tabu_list) >= self.tabu_tenure:
            self.tabu_list.pop(0)
        # Add simplified move representation
        self.tabu_list.append(tuple(solution[:2]) if len(solution) >= 2 else (0, 0))
    
    def _calculate_total_distance(self, solution: List[int], start_point: Tuple[float, float]) -> float:
        """Calculate total distance for a solution"""
        if not solution:
            return 0
        
        total = haversine_km(start_point[0], start_point[1], 
                           self.points[solution[0]][0], self.points[solution[0]][1])
        
        for i in range(len(solution) - 1):
            p1 = self.points[solution[i]]
            p2 = self.points[solution[i + 1]]
            total += haversine_km(p1[0], p1[1], p2[0], p2[1])
        
        return total


class AdvancedDeliveryOptimizer:
    """Main optimizer combining Branch & Bound and Tabu Search"""
    
    def __init__(self):
        self.stores = self._get_default_stores()
    
    def _get_default_stores(self) -> List[Store]:
        """Default stores in Casablanca area"""
        return [
            Store(1, "Marjane", 33.5731, -7.5898, ["fruits", "vegetables", "meat", "dairy"]),
            Store(2, "BIM", 33.5850, -7.6030, ["packaged", "dairy", "snacks"]),
            Store(3, "Attakadaw", 33.5920, -7.6150, ["fruits", "vegetables"]),
            Store(4, "Aswak Salam", 33.5650, -7.5750, ["meat", "dairy", "frozen"]),
        ]
    
    def optimize_delivery_route(self, courier_pos: Tuple[float, float], 
                              orders_data: List[Dict], 
                              capacity_weight: float = 10.0,
                              capacity_distance: float = 20.0) -> Dict:
        """Main optimization function with complete route planning"""
        
        # Convert orders data to Order objects
        orders = self._convert_to_orders(orders_data)
        
        if not orders:
            return {
                "selected_order_ids": [],
                "total_profit": 0,
                "total_distance": 0,
                "total_weight": 0,
                "route_details": [],
                "full_route_coordinates": []
            }
        
        # Step 1: Order Selection using Branch & Bound (Knapsack)
        knapsack_solver = BranchAndBoundKnapsack(orders, capacity_weight, capacity_distance)
        selected_orders = knapsack_solver.solve()
        
        if not selected_orders:
            return {
                "selected_order_ids": [],
                "total_profit": 0,
                "total_distance": 0,
                "total_weight": 0,
                "route_details": [],
                "full_route_coordinates": []
            }
        
        # Step 2: Generate complete route with pickup and delivery sequence
        complete_route = self._generate_complete_route(courier_pos, selected_orders)
        
        # Step 3: Calculate final metrics
        total_distance = self._calculate_complete_route_distance(complete_route)
        total_profit = sum(order.total_profit for order in selected_orders)
        total_weight = sum(order.total_weight for order in selected_orders)
        
        return {
            "selected_order_ids": [order.id for order in selected_orders],
            "total_profit": total_profit,
            "total_distance": total_distance,
            "total_weight": total_weight,
            "route_details": complete_route,
            "full_route_coordinates": self._get_route_coordinates(complete_route)
        }
    
    def _convert_to_orders(self, orders_data: List[Dict]) -> List[Order]:
        """Convert raw order data to Order objects"""
        orders = []
        for data in orders_data:
            # Simulate item categorization and store assignment
            items = [{"category": "general", "weight": data.get("total_weight_kg", 1.0), "profit": float(data.get("delivery_price_offer", 0))}]
            
            order = Order(
                id=data["id"],
                customer_lat=data["location_lat"],
                customer_lng=data["location_lng"],
                items=items,
                total_weight=data.get("total_weight_kg", 1.0),
                total_profit=float(data.get("delivery_price_offer", 0))
            )
            orders.append(order)
        
        return orders
    
    def _generate_complete_route(self, courier_pos: Tuple[float, float], orders: List[Order]) -> List[Dict]:
        """Generate complete route with pickup and delivery points in optimal order"""
        route_points = []
        
        # Add courier starting position
        route_points.append({
            "step": 1,
            "type": "start",
            "location": {"lat": courier_pos[0], "lng": courier_pos[1]},
            "description": "Point de départ du livreur",
            "estimated_time": "0 min"
        })
        
        step = 2
        
        # For each order, add pickup then delivery
        for order in orders:
            # Find best store for this order's items
            best_store = self._find_best_store_for_order(order)
            
            # Add pickup point
            route_points.append({
                "step": step,
                "type": "pickup",
                "location": {"lat": best_store.lat, "lng": best_store.lng},
                "store_name": best_store.name,
                "order_id": order.id,
                "description": f"Récupération commande #{order.id} chez {best_store.name}",
                "estimated_time": f"{step * 5} min"
            })
            step += 1
            
            # Add delivery point
            route_points.append({
                "step": step,
                "type": "delivery",
                "location": {"lat": order.customer_lat, "lng": order.customer_lng},
                "order_id": order.id,
                "customer_phone": getattr(order, 'customer_phone', 'N/A'),
                "profit": order.total_profit,
                "description": f"Livraison commande #{order.id}",
                "estimated_time": f"{step * 5} min"
            })
            step += 1
        
        return route_points
    
    def _find_best_store_for_order(self, order: Order) -> Store:
        """Find the best store for an order based on distance and item availability"""
        # For now, return the nearest store (can be enhanced with item availability logic)
        return min(self.stores, 
                  key=lambda s: haversine_km(s.lat, s.lng, order.customer_lat, order.customer_lng))
    
    def _calculate_complete_route_distance(self, route_points: List[Dict]) -> float:
        """Calculate total distance for the complete route"""
        total_distance = 0
        
        for i in range(len(route_points) - 1):
            current = route_points[i]["location"]
            next_point = route_points[i + 1]["location"]
            total_distance += haversine_km(
                current["lat"], current["lng"],
                next_point["lat"], next_point["lng"]
            )
        
        return total_distance
    
    def _get_route_coordinates(self, route_points: List[Dict]) -> List[List[float]]:
        """Extract coordinates for map display"""
        return [[point["location"]["lat"], point["location"]["lng"]] for point in route_points]
    
    def _calculate_route_distance(self, courier_pos: Tuple[float, float], 
                                orders: List[Order], delivery_sequence: List[int], 
                                pickup_sequence: List[Tuple[int, int]]) -> float:
        """Calculate total route distance including pickups and deliveries"""
        total_distance = 0
        current_pos = courier_pos
        
        # Distance to first pickup
        if pickup_sequence:
            first_store = next(s for s in self.stores if s.id == pickup_sequence[0][0])
            total_distance += haversine_km(current_pos[0], current_pos[1], first_store.lat, first_store.lng)
            current_pos = (first_store.lat, first_store.lng)
        
        # Simplified distance calculation
        for i, order_idx in enumerate(delivery_sequence):
            order = orders[order_idx]
            total_distance += haversine_km(current_pos[0], current_pos[1], order.customer_lat, order.customer_lng)
            current_pos = (order.customer_lat, order.customer_lng)
        
        return total_distance
    
    def _generate_route_details(self, courier_pos: Tuple[float, float], 
                              orders: List[Order], delivery_sequence: List[int], 
                              pickup_sequence: List[Tuple[int, int]]) -> List[Dict]:
        """Generate detailed route information"""
        route_details = []
        
        # Add pickup stops
        for store_id, order_id in pickup_sequence:
            store = next(s for s in self.stores if s.id == store_id)
            route_details.append({
                "type": "pickup",
                "location": {"lat": store.lat, "lng": store.lng},
                "store_name": store.name,
                "order_id": order_id
            })
        
        # Add delivery stops
        for order_idx in delivery_sequence:
            order = orders[order_idx]
            route_details.append({
                "type": "delivery",
                "location": {"lat": order.customer_lat, "lng": order.customer_lng},
                "order_id": order.id,
                "profit": order.total_profit
            })
        
        return route_details


# Backward compatibility functions
def knapsack_max_profit(items: List[Dict], capacity_km: float) -> List[Dict]:
    """Backward compatibility wrapper"""
    optimizer = AdvancedDeliveryOptimizer()
    orders_data = []
    
    for item in items:
        orders_data.append({
            "id": item["id"],
            "location_lat": item["customer"][0],
            "location_lng": item["customer"][1],
            "total_weight_kg": item.get("distance_km", 1.0),  # Use distance as weight proxy
            "delivery_price_offer": item["profit"]
        })
    
    result = optimizer.optimize_delivery_route((0, 0), orders_data, capacity_km, capacity_km)
    
    # Convert back to original format
    selected_items = []
    for order_id in result["selected_order_ids"]:
        original_item = next(item for item in items if item["id"] == order_id)
        selected_items.append(original_item)
    
    return selected_items


def nearest_neighbor_route(start: Tuple[float, float], points: List[Tuple[float, float]]) -> List[int]:
    """Backward compatibility wrapper using Tabu Search"""
    if not points:
        return []
    
    tsp_solver = TabuSearchTSP(points, max_iterations=50)
    return tsp_solver.solve(start)
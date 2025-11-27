from typing import List, Tuple
from math import radians, sin, cos, sqrt, atan2
from .models import Order

def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate the great-circle distance between two points on the Earth surface."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # Earth radius in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

class KnapsackNode:
    def __init__(self, level: int, profit: float, weight: float, bound: float, taken: List[int]):
        self.level = level
        self.profit = profit
        self.weight = weight
        self.bound = bound
        self.taken = taken

def compute_bound(node: KnapsackNode, n: int, capacity: float, items: List[Tuple[int, float, float]]) -> float:
    if node.weight >= capacity:
        return 0
    profit_bound = node.profit
    totweight = node.weight
    j = node.level + 1
    while j < n and totweight + items[j][2] <= capacity:
        totweight += items[j][2]
        profit_bound += items[j][1]
        j += 1
    if j < n:
        profit_bound += (capacity - totweight) * (items[j][1] / items[j][2])
    return profit_bound

def knapsack_branch_and_bound(capacity: float, orders: List[Order]) -> List[Order]:
    if not orders:
        return []

    # items: (original_index, value, weight)
    items = [(i, order.delivery_price_offer, order.estimated_weight_kg()) for i, order in enumerate(orders)]
    n = len(items)
    # Sort by value/weight ratio descending
    items.sort(key=lambda x: x[1] / x[2], reverse=True)

    max_profit = 0.0
    best_taken = []

    # BFS queue
    queue = []
    root = KnapsackNode(-1, 0.0, 0.0, 0.0, [])
    root.bound = compute_bound(root, n, capacity, items)
    queue.append(root)

    while queue:
        u = queue.pop(0)  # FIFO for BFS

        if u.level == n - 1:
            continue

        # Branch: take the item
        v_level = u.level + 1
        v_weight = u.weight + items[v_level][2]
        v_profit = u.profit + items[v_level][1]
        v_taken = u.taken + [v_level]

        if v_weight <= capacity and v_profit > max_profit:
            max_profit = v_profit
            best_taken = v_taken

        v = KnapsackNode(v_level, v_profit, v_weight, 0.0, v_taken)
        v.bound = compute_bound(v, n, capacity, items)
        if v.bound > max_profit:
            queue.append(v)

        # Branch: don't take the item
        w = KnapsackNode(v_level, u.profit, u.weight, 0.0, u.taken[:])
        w.bound = compute_bound(w, n, capacity, items)
        if w.bound > max_profit:
            queue.append(w)

    # Map back to original orders using original indices
    selected_indices = [items[i][0] for i in best_taken]
    selected_orders = [orders[idx] for idx in selected_indices]

    return selected_orders

def tsp_nearest_neighbor(courier_location: Tuple[float, float], orders: List[Order]) -> List[Tuple[float, float]]:
    """Simple nearest neighbor heuristic for TSP, starting from courier location."""
    # Collect all points: stores and client locations
    points = set()
    for order in orders:
        if order.store:
            points.add((order.store.location_lat, order.store.location_lng))
        points.add((order.location_lat, order.location_lng))
    unvisited = list(points)
    
    if not unvisited:
        return [courier_location]

    path = [courier_location]
    current = courier_location

    while unvisited:
        # Find nearest unvisited point
        nearest = min(unvisited, key=lambda p: haversine(current, p))
        path.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return path
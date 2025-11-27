import math
from typing import List, Dict, Tuple


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def order_distance_km(courier: Tuple[float, float], customer: Tuple[float, float], restaurant: Tuple[float, float] | None) -> float:
    clat, clng = courier
    plat, plng = customer
    if restaurant and restaurant[0] is not None and restaurant[1] is not None:
        rlat, rlng = restaurant
        return haversine_km(clat, clng, rlat, rlng) + haversine_km(rlat, rlng, plat, plng)
    return haversine_km(clat, clng, plat, plng)


def knapsack_max_profit(items: List[Dict], capacity_km: float) -> List[Dict]:
    # items: [{id, profit, distance_km}]
    n = len(items)
    # scale distances to integers to use DP; granularity 0.1 km
    scale = 10
    W = int(capacity_km * scale)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    keep = [[False] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w_i = int(items[i - 1]["distance_km"] * scale)
        v_i = float(items[i - 1]["profit"])  # profit as float
        for w in range(W + 1):
            if w_i <= w and dp[i - 1][w - w_i] + v_i > dp[i - 1][w]:
                dp[i][w] = dp[i - 1][w - w_i] + v_i
                keep[i][w] = True
            else:
                dp[i][w] = dp[i - 1][w]
    # reconstruct
    res: List[Dict] = []
    w = W
    for i in range(n, 0, -1):
        if keep[i][w]:
            res.append(items[i - 1])
            w -= int(items[i - 1]["distance_km"] * scale)
    res.reverse()
    return res


def nearest_neighbor_route(start: Tuple[float, float], points: List[Tuple[float, float]]) -> List[int]:
    # returns order of indices into points by nearest neighbor
    remaining = list(range(len(points)))
    route: List[int] = []
    current = start
    while remaining:
        nearest_idx = min(remaining, key=lambda idx: haversine_km(current[0], current[1], points[idx][0], points[idx][1]))
        route.append(nearest_idx)
        current = points[nearest_idx]
        remaining.remove(nearest_idx)
    return route

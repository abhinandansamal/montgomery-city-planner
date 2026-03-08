"""Mock data services for advanced Montgomery City Planner features.

These functions provide synthetic data for endpoints that do not exist in the
real Montgomery ArcGIS FeatureServers, allowing the UI to demonstrate
advanced features like walkability isochrones, 311 liability heatmaps,
and school zone buffers.
"""

import math
import random
from typing import Any, Dict, List


def _generate_polygon(lat: float, lon: float, radius_meters: float, points: int = 16) -> List[List[float]]:
    """Generate a rough polygon approximating a circle around a point.

    Args:
        lat: Center latitude.
        lon: Center longitude.
        radius_meters: Radius in meters.
        points: Number of vertices for the polygon.

    Returns:
        A list of [lat, lon] coordinates representing the closed polygon.
    """
    polygon = []
    # Earth radius in meters
    R = 6378137
    for i in range(points):
        angle = math.pi * 2 * i / points
        dx = radius_meters * math.cos(angle)
        dy = radius_meters * math.sin(angle)
        
        plat = lat + (dy / R) * (180 / math.pi)
        plon = lon + (dx / R) * (180 / math.pi) / math.cos(lat * math.pi / 180)
        polygon.append([plat, plon])
    
    # Close polygon
    polygon.append(polygon[0])
    return polygon


async def query_walkability_isochrones(lat: float, lon: float) -> str:
    """Generate mock walkability isochrones (5, 10, 15 min walks) for a location.
    
    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).
        
    Returns:
        JSON-style string containing the isochrone definitions to plot on the map.
    """
    # 5 min walk ~ 400m
    # 10 min walk ~ 800m
    # 15 min walk ~ 1200m
    
    def _noisy_polygon(radius: float) -> List[List[float]]:
        poly = []
        R = 6378137
        points = 24
        for i in range(points):
            angle = math.pi * 2 * i / points
            # Add some noise to radius to make it look organic
            r = radius * random.uniform(0.7, 1.2)
            dx = r * math.cos(angle)
            dy = r * math.sin(angle)
            
            plat = lat + (dy / R) * (180 / math.pi)
            plon = lon + (dx / R) * (180 / math.pi) / math.cos(lat * math.pi / 180)
            poly.append([plat, plon])
        poly.append(poly[0])
        return poly

    isochrones = [
        {"time": 5, "coords": _noisy_polygon(400), "color": "#10b981"},  # Green
        {"time": 10, "coords": _noisy_polygon(800), "color": "#f59e0b"}, # Yellow
        {"time": 15, "coords": _noisy_polygon(1200), "color": "#3b82f6"}, # Blue
    ]
    
    return str(isochrones)


async def query_311_reports(lat: float, lon: float, radius_meters: int = 1000) -> str:
    """Find recent 311 municipal service requests and aggregate costs near a location.
    
    Useful for identifying "Money Pits" (high liability properties).
    
    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).
        radius_meters: Search radius in meters.
        
    Returns:
        A human-readable summary of 311 reports and estimated annual maintenance costs.
    """
    # Generate deterministic-feeling mock data based on location
    seed = int((lat + lon) * 100000 % 10000)
    random.seed(seed)
    
    num_incidents = random.randint(3, 15)
    incident_types = ["Illegal Dumping", "Overgrown Lot", "Abandoned Vehicle", "Code Violation", "Graffiti"]
    
    total_cost = 0
    incidents = []
    
    for _ in range(num_incidents):
        itype = random.choice(incident_types)
        
        # Assign random costs
        if itype == "Illegal Dumping":
            cost = random.randint(500, 2000)
        elif itype == "Overgrown Lot":
            cost = random.randint(300, 1000)
        else:
            cost = random.randint(100, 500)
            
        total_cost += cost
        
        # Generate random coordinate near lat/lon
        dx = random.uniform(-radius_meters, radius_meters)
        dy = random.uniform(-radius_meters, radius_meters)
        R = 6378137
        plat = lat + (dy / R) * (180 / math.pi)
        plon = lon + (dx / R) * (180 / math.pi) / math.cos(lat * math.pi / 180)
        
        incidents.append({
            "type": itype,
            "cost": cost,
            "lat": plat,
            "lon": plon
        })

    random.seed()  # Restore random state
    
    summary = (
        f"Found {len(incidents)} severe 311 reports within {radius_meters}m.\n"
        f"Estimated annual city maintenance cost: ${total_cost:,}\n"
        f"Breakdown:\n"
    )
    
    # Summarize top 3
    incidents.sort(key=lambda x: x["cost"], reverse=True)
    for i, inc in enumerate(incidents[:3], 1):
        summary += f"{i}. {inc['type']} — Cost: ${inc['cost']} | Coord: {inc['lat']:.5f}, {inc['lon']:.5f}\n"

    return summary


async def query_schools_and_buffers(lat: float, lon: float) -> str:
    """Find schools near a location and define protective buffer zones.
    
    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).
        
    Returns:
        JSON-style string containing school details and protective buffer polygons.
    """
    schools = [
        {"name": "Bellingrath Middle School", "lat": 32.348, "lon": -86.314},
        {"name": "Booker T Washington Magnet", "lat": 32.361, "lon": -86.305},
        {"name": "Sidney Lanier High School", "lat": 32.365, "lon": -86.319},
        {"name": "Davis Elementary School", "lat": 32.385, "lon": -86.299},
    ]
    
    # Find the closest school
    closest = None
    min_dist = float('inf')
    
    for s in schools:
        dist = (s["lat"] - lat)**2 + (s["lon"] - lon)**2
        if dist < min_dist:
            min_dist = dist
            closest = s
            
    if not closest or min_dist > 0.005:  # ~5km
        return "No schools found close enough to trigger protective buffers."
        
    # Generate a tight protective buffer (500m)
    buffer_polygon = _generate_polygon(closest["lat"], closest["lon"], 500)
    
    result = {
        "school": closest["name"],
        "school_lat": closest["lat"],
        "school_lon": closest["lon"],
        "buffer_radius_m": 500,
        "buffer_polygon": buffer_polygon
    }
    
    return str(result)

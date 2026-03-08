"""ArcGIS Zoning and spatial query tools for Montgomery, AL.

Queries the Montgomery Zoning FeatureServer for zoning classifications
and performs spatial point-in-polygon lookups.
"""

from typing import Any, Dict, List
import httpx

# Montgomery ArcGIS Zoning FeatureServer URL
ZONING_URL = (
    "https://gis.montgomeryal.gov/server/rest/services/"
    "Zoning/FeatureServer/0/query"
)


async def query_zoning_by_point(lat: float, lon: float) -> Dict[str, Any]:
    """Perform a spatial point-in-polygon query for zoning at a coordinate.

    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).

    Returns:
        A dictionary containing zoning details:
            - zone_code (str): The zoning classification code (e.g., 'T4-O').
            - zone_name (str): Full description of the zone.
            - ordinance (str): Municipal ordinance number.
            - ord_date (str): Date the ordinance was passed.
    """
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ZoningCode,ZoningDesc,Ordinance,Ord_Date",
        "f": "json",
        "returnGeometry": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(ZONING_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return {
            "zone_code": "ERROR",
            "zone_name": f"Query failed: {str(e)}",
            "ordinance": "N/A",
            "ord_date": "N/A",
        }

    if "error" in data:
        return {
            "zone_code": "ERROR",
            "zone_name": data["error"].get("message", "Unknown error"),
            "ordinance": "N/A",
            "ord_date": "N/A",
        }

    features = data.get("features", [])
    if not features:
        return {
            "zone_code": "NONE",
            "zone_name": "No zoning data at this location",
            "ordinance": "N/A",
            "ord_date": "N/A",
        }

    attrs = features[0].get("attributes", {})
    return {
        "zone_code": attrs.get("ZoningCode", "N/A"),
        "zone_name": attrs.get("ZoningDesc", "N/A"),
        "ordinance": attrs.get("Ordinance", "N/A"),
        "ord_date": attrs.get("Ord_Date", "N/A"),
    }


async def query_zoning_by_code(code: str, max_records: int = 20) -> List[Dict[str, Any]]:
    """Query all zones matching a zoning code pattern.

    Args:
        code: Zoning code to search (e.g., 'C-2', 'T4', 'R-1').
        max_records: Maximum records to return.

    Returns:
        List of dictionaries where each dict contains zoning classification details.
    """
    safe_code = code.upper().replace("'", "''")
    params = {
        "where": f"UPPER(ZoningCode) LIKE '%{safe_code}%'",
        "outFields": "ZoningCode,ZoningDesc,Ordinance,Ord_Date",
        "resultRecordCount": max_records,
        "f": "json",
        "returnGeometry": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(ZONING_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return [{"error": f"ArcGIS query failed: {str(e)}"}]

    if "error" in data:
        return [{"error": f"ArcGIS error: {data['error'].get('message', str(data['error']))}"}]

    features = data.get("features", [])
    results: List[Dict[str, Any]] = []
    for feat in features:
        attrs = feat.get("attributes", {})
        results.append({
            "zone_code": attrs.get("ZoningCode", "N/A"),
            "zone_name": attrs.get("ZoningDesc", "N/A"),
            "ordinance": attrs.get("Ordinance", "N/A"),
            "ord_date": attrs.get("Ord_Date", "N/A"),
        })

    return results

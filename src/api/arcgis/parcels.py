"""ArcGIS Parcel and Property query tools for Montgomery, AL.

Queries the Montgomery County Parcels FeatureServer to find properties
by owner name, address, neighborhood, or value range.
"""

from typing import Any, List, Dict, Optional
import httpx

# Montgomery ArcGIS Parcels FeatureServer URL
PARCELS_URL = (
    "https://gis.montgomeryal.gov/server/rest/services/"
    "Parcels/FeatureServer/0/query"
)


async def query_parcels(
    keyword: str = "",
    neighborhood: str = "",
    max_value: float = 0,
    max_records: int = 50,
) -> List[Dict[str, Any]]:
    """Query Montgomery parcels with flexible filtering.

    Args:
        keyword: Search term for owner name or property address.
        neighborhood: Filter by neighborhood code.
        max_value: If > 0, filter for properties with TotalValue <= this.
        max_records: Maximum records to return.

    Returns:
        List of parcel dicts with standardized fields. Each dict contains:
            - parcel_id (str): The unique parcel identifier.
            - owner (str): Owner name.
            - address (str): Full property address.
            - neighborhood (str): Neighborhood code.
            - acreage (float): Size in acres.
            - land_value (float): Market land value.
            - improvement_value (float): Value of structures.
            - total_value (float): Total market value.
            - assessment_class (str): Assessment classification.
            - lat (float): Latitude.
            - lon (float): Longitude.
    """
    clauses = []
    if keyword:
        safe_kw = keyword.upper().replace("'", "''")
        clauses.append(
            f"(UPPER(OwnerName) LIKE '%{safe_kw}%' "
            f"OR UPPER(PropertyAddr1) LIKE '%{safe_kw}%')"
        )
    if neighborhood:
        safe_nb = neighborhood.upper().replace("'", "''")
        clauses.append(f"UPPER(Neighborhood) LIKE '%{safe_nb}%'")
    if max_value > 0:
        clauses.append(f"TotalValue <= {max_value}")

    where = " AND ".join(clauses) if clauses else "1=1"

    params = {
        "where": where,
        "outFields": (
            "ParcelNo,OwnerName,PropertyAddr1,PropertyCity,PropertyZip,"
            "Neighborhood,Calc_Acre,TotalLandValue,TotalImpValue,TotalValue,"
            "AssessmentClass"
        ),
        "resultRecordCount": max_records,
        "f": "json",
        "returnGeometry": "true",
        "outSR": "4326",
        "returnCentroid": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(PARCELS_URL, params=params)
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
        geom = feat.get("geometry", {})

        # Handle polygon geometry — get centroid
        lat, lon = None, None
        if "y" in geom and "x" in geom:
            lat, lon = geom["y"], geom["x"]
        elif "rings" in geom and geom["rings"]:
            # Calculate centroid from polygon rings
            ring = geom["rings"][0]
            if ring:
                avg_x = sum(p[0] for p in ring) / len(ring)
                avg_y = sum(p[1] for p in ring) / len(ring)
                lat, lon = avg_y, avg_x

        owner = (attrs.get("OwnerName") or "Unknown").strip()
        address = (attrs.get("PropertyAddr1") or "N/A").strip()
        city = (attrs.get("PropertyCity") or "Montgomery").strip()

        results.append({
            "parcel_id": (attrs.get("ParcelNo") or "N/A").strip(),
            "owner": owner,
            "address": f"{address}, {city}",
            "neighborhood": (attrs.get("Neighborhood") or "N/A").strip(),
            "acreage": round(attrs.get("Calc_Acre", 0) or 0, 2),
            "land_value": attrs.get("TotalLandValue", 0) or 0,
            "improvement_value": attrs.get("TotalImpValue", 0) or 0,
            "total_value": attrs.get("TotalValue", 0) or 0,
            "assessment_class": attrs.get("AssessmentClass", "N/A"),
            "lat": lat,
            "lon": lon,
        })

    return results


async def query_vacant_parcels(
    neighborhood: str = "",
    max_records: int = 50,
) -> List[Dict[str, Any]]:
    """Find likely vacant/unimproved parcels (improvement value = 0).

    Args:
        neighborhood: Optional neighborhood filter.
        max_records: Maximum records to return.

    Returns:
        List of vacant parcel dicts with geographic coordinates.
    """
    clauses = ["TotalImpValue = 0", "Calc_Acre > 0"]
    if neighborhood:
        safe_nb = neighborhood.upper().replace("'", "''")
        clauses.append(f"UPPER(Neighborhood) LIKE '%{safe_nb}%'")

    where = " AND ".join(clauses)

    params = {
        "where": where,
        "outFields": (
            "ParcelNo,OwnerName,PropertyAddr1,PropertyCity,PropertyZip,"
            "Neighborhood,Calc_Acre,TotalLandValue,TotalImpValue,TotalValue,"
            "AssessmentClass"
        ),
        "resultRecordCount": max_records,
        "f": "json",
        "returnGeometry": "true",
        "outSR": "4326",
        "orderByFields": "Calc_Acre DESC",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(PARCELS_URL, params=params)
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
        geom = feat.get("geometry", {})

        lat, lon = None, None
        if "rings" in geom and geom["rings"]:
            ring = geom["rings"][0]
            if ring:
                avg_x = sum(p[0] for p in ring) / len(ring)
                avg_y = sum(p[1] for p in ring) / len(ring)
                lat, lon = avg_y, avg_x

        results.append({
            "parcel_id": (attrs.get("ParcelNo") or "N/A").strip(),
            "owner": (attrs.get("OwnerName") or "Unknown").strip(),
            "address": (attrs.get("PropertyAddr1") or "N/A").strip(),
            "neighborhood": (attrs.get("Neighborhood") or "N/A").strip(),
            "acreage": round(attrs.get("Calc_Acre", 0) or 0, 2),
            "land_value": attrs.get("TotalLandValue", 0) or 0,
            "total_value": attrs.get("TotalValue", 0) or 0,
            "lat": lat,
            "lon": lon,
        })

    return results

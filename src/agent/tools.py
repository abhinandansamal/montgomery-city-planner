"""LangGraph tool definitions for The Montgomery City Planner.

This module contains the logic to wrap city planner functions as LangChain tools
and provides a centralized registration hook for the MCP server.
"""

from typing import Any, List, Optional
from langchain_core.tools import tool

from src.api.arcgis.parcels import query_parcels, query_vacant_parcels
from src.api.arcgis.zoning import query_zoning_by_point
from src.api.search.brightdata import trigger_brightdata_scrape
from src.rag.engine import search_city_policy
from src.utils.mock_data import (
    query_walkability_isochrones,
    query_311_reports,
    query_schools_and_buffers
)


async def search_parcels_func(keyword: str, max_records: int = 50) -> str:
    """Search Montgomery parcels by owner name or property address.

    Args:
        keyword: Search term for owner name or property address (e.g. 'DEXTER AVE', 'CITY OF MONTGOMERY').
        max_records: Maximum results to return.

    Returns:
        A formatted string summarizing the found parcels.
    """
    try:
        records = await query_parcels(keyword=keyword, max_records=max_records)
        if not records:
            return f"No parcels found matching '{keyword}'."
        if "error" in records[0]:
            return f"Error: {records[0]['error']}"
        lines = [f"Found {len(records)} parcel(s) for '{keyword}':\n"]
        for i, r in enumerate(records, 1):
            lines.append(
                f"{i}. {r['owner']} — {r['address']}\n"
                f"   Parcel: {r['parcel_id']} | {r['acreage']} acres | "
                f"Value: ${r['total_value']:,.0f} | ({r['lat']}, {r['lon']})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error querying parcels: {str(e)}"


async def search_vacant_parcels_func(neighborhood: str = "", max_records: int = 50) -> str:
    """Find vacant/unimproved parcels (no structures) in Montgomery.

    Args:
        neighborhood: Optional neighborhood code to filter by.
        max_records: Maximum results to return.

    Returns:
        A formatted string summarizing the found vacant parcels.
    """
    try:
        records = await query_vacant_parcels(neighborhood, max_records)
        if not records:
            return "No vacant parcels found."
        if "error" in records[0]:
            return f"Error: {records[0]['error']}"
        lines = [f"Found {len(records)} vacant parcel(s):\n"]
        for i, r in enumerate(records, 1):
            lines.append(
                f"{i}. {r['address']} — Owner: {r['owner']}\n"
                f"   Parcel: {r['parcel_id']} | {r['acreage']} acres | "
                f"Land Value: ${r['land_value']:,.0f} | ({r['lat']}, {r['lon']})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error querying vacant parcels: {str(e)}"


async def check_zoning_func(lat: float, lon: float) -> str:
    """Check zoning classification for a specific coordinate in Montgomery.

    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).

    Returns:
        A formatted string with the zone code and description.
    """
    try:
        r = await query_zoning_by_point(lat, lon)
        return (
            f"Zone: {r['zone_code']} — {r['zone_name']}\n"
            f"Ordinance: {r['ordinance']} (Date: {r['ord_date']})"
        )
    except Exception as e:
        return f"Error querying zoning: {str(e)}"


async def live_web_search_func(query: str, location: str = "Montgomery, AL") -> str:
    """Perform a live web search to verify businesses or find retail gaps.

    Use this to cross-reference business names against live web presence
    (ghost business detection) or to find retail establishments in an area.

    Args:
        query: Search query (e.g. 'pharmacy near West Montgomery').
        location: Location context for the search.

    Returns:
        A formatted string with web results.
    """
    try:
        results = await trigger_brightdata_scrape(query, location)
        if not results:
            return f"No organic search results found for '{query}' on the live web."
        if isinstance(results, list) and len(results) > 0 and "error" in results[0]:
            return f"Web search tool error: {results[0]['error']}. Fall back to official parcel data."
        lines = [f"Web results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']} — {r['link']}\n   {r['snippet']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Live web search tool is currently offline: {str(e)}. Proceeding with city data only."


async def search_policy_func(query: str, n_results: int = 5) -> str:
    """Search Montgomery zoning/planning policy documents.

    Args:
        query: Natural-language question about city policy.
        n_results: Number of excerpts to retrieve.

    Returns:
        A formatted string with policy excerpts and citations.
    """
    try:
        results = await search_city_policy(query, n_results)
        if not results:
            return "No policy documents found."
        if "error" in results[0]:
            return results[0]["error"]
        lines = [f"Policy results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r['source']} p.{r['page']}] {r['text'][:200]}...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching policy documents: {str(e)}"


# --- Raw functions for MCP registration ---
RAW_FUNCTIONS = [
    search_parcels_func,
    search_vacant_parcels_func,
    check_zoning_func,
    live_web_search_func,
    search_policy_func,
    query_walkability_isochrones,
    query_311_reports,
    query_schools_and_buffers,
]

# --- Wrapped tools for LangGraph agent ---
TOOLS = [tool(f) for f in RAW_FUNCTIONS]

# Keep exports for existing tools if needed by name, but usually TOOLS list is used
search_parcels = tool(search_parcels_func)
search_vacant_parcels = tool(search_vacant_parcels_func)
check_zoning = tool(check_zoning_func)
live_web_search = tool(live_web_search_func)
search_policy = tool(search_policy_func)


def register_all_tools(mcp: Any) -> None:
    """Register all available Montgomery City Planner tools with an MCP server instance.

    Args:
        mcp: The FastMCP server instance where tools will be registered.
    """
    for f in RAW_FUNCTIONS:
        mcp.tool()(f)

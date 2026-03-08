"""Montgomery City Planner — FastAPI MCP Server.

Hosts a Model Context Protocol (MCP) server over Server-Sent Events (SSE).
Registers all urban-planning tools: ArcGIS queries, Bright Data scraping,
and ChromaDB policy search.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp_server = FastMCP("MontgomeryPlanner")

# ---------------------------------------------------------------------------
# Register tools — centralized registration from the agent tools module
# ---------------------------------------------------------------------------
from src.agent.tools import register_all_tools

register_all_tools(mcp_server)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    yield

app = FastAPI(
    title="Montgomery City Planner — MCP Server",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount MCP endpoints
# ---------------------------------------------------------------------------
@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP server communication."""
    return await mcp_server.handle_sse()


@app.post("/messages/")
async def messages_endpoint():
    """POST endpoint for MCP message handling."""
    return await mcp_server.handle_message()


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok", "service": "montgomery-city-planner"}

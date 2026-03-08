# 🏛️ Montgomery City Planner: Architecture & Data Specifications

The Montgomery City Planner is built on a resilient, modular architecture that bridges high-level AI reasoning with low-level geospatial APIs. This document outlines the technical underpinnings, data sources, and algorithmic logic driving the application.

---

## 🏗️ Core Architecture

The system is separated into three distinct layers to ensure scalability and reliability:

1. **The Presentation Layer (`app.py`)**
   - **Framework**: Streamlit
   - **Functionality**: Provides the "Command Center" UI, rendering the 30/70 split-screen chat and interactive map.
   - **Map Engine**: Folium handles dynamic pin drops (e.g., pulsing red for liabilities, gradient for future zoning) and polygon overlays based on AI `TRIGGER_MAP` payloads.

2. **The Orchestration Layer (`src/agent/`)**
   - **Framework**: LangGraph
   - **Pattern**: Stateful agent executing a `ReAct` (Reasoning + Acting) loop.
   - **Resilience**: A sequential LLM fallback chain. If Groq (Llama 3) hits a rate limit or fails, the graph automatically delegates to OpenAI (GPT-4o), and then to Anthropic (Claude 3.5 Sonnet).
   - **State**: The `AgentState` manages the conversational memory and the extracted `map_triggers` for the UI.

3. **The Data Services Layer (`src/api/` & `src/rag/`)**
   - **Framework**: FastMCP (Model Context Protocol) Server.
   - **Functionality**: Exposes external APIs and internal RAG databases as LangChain tools. Centralizes data fetching logic away from the core reasoning engine.

---

## 🗄️ Dataset Specifications

The agent relies on a fusion of real-world municipal APIs and simulated data to generate its insights:

### 1. ArcGIS Montgomery REST API
- **Endpoint**: `https://services.arcgis.com/.../FeatureServer/0/query`
- **Data Extracted**: Parcels, Land Values, Assessed Acreage, Owner Names, and Coordinates.
- **Usage**: Ground-truth for "Ghost Business" and "Clean Slate Inventory" modules.

### 2. Bright Data SERP Scraper
- **Service**: Real-time Google Search Engine Results Page (SERP) API.
- **Usage**: Used to verify the physical existence of a business by cross-referencing parcel owner names against live web presence. 
- **Caching**: Results are cached locally in `scrape_cache.db` to minimize API costs and latency during repetitive queries.

### 3. Policy Vector Database (ChromaDB + RAG)
- **Source**: `data_files/comp_plan.pdf` (Montgomery 2020 Comprehensive Plan) and `data_files/zoning.pdf` (Zoning Ordinances).
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace.
- **Usage**: Allows the agent to answer complex regulatory questions using vector similarity search (e.g., "What is the maximum height in a T4-O zone?").

### 4. Custom Mock Data Generators
- **311 Liability**: Simulates property code violations, illegal dumping, and structural damages using weighted randomness to identify "Money Pit" parcels.
- **Walkability Isochrones**: Generates synthetic 15-minute city polygons (using Shapely and PyProj) to simulate pedestrian accessibility.
- **School Safety Buffers**: Calculates 500ft safety radiuses around educational zones.

---

## 🧠 Key Algorithmic Logic

### Ghost Business Detection Pipeline
The most complex reasoning loop in the application involves separating active businesses from "ghosts" (properties sitting idle on the city record).
1. **Trigger**: User queries "Find ghost businesses in Downtown."
2. **Action 1 (Retrieve Official Data)**: Agent calls `search_parcels(keyword='DOWNTOWN')`.
3. **Internal Filtering**: The agent extracts up to 10-15 official business owners.
4. **Action 2 (Live Verification)**: The agent iteratively calls `live_web_search_func` for *every* extracted business name.
5. **Logic Gate**: 
   - If `Live Web Search` returns > 0 relevant hits = Active Business.
   - If `Live Web Search` returns 0 hits ("No organic search results") = **Ghost Business**.
6. **Execution**: The agent logs the Ghost Business in its markdown table and outputs a JSON `TRIGGER_MAP` dropping a red `remove-sign` pin at the parcel's precise latitude/longitude.

### The JSON Parsing Engine
To prevent technical data from leaking into the UI, a robust `json.JSONDecoder().raw_decode()` pipeline operates in `app.py`.
- **Flexibility**: It dynamically scans for LLM formatting deviations (e.g., `<TRIGGER_MAP>`, `TRIGGER_MAP:`).
- **Depth**: It parses deeply nested arrays containing hundreds of map coordinates.
- **Sanitization**: It identifies the exact character span of the JSON block and strips it entirely from the Streamlit markdown output, maintaining a professional "Copilot" aesthetic.

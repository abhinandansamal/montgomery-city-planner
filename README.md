# 🏙️ Montgomery City Planner: AI Urban Command Center

A high-performance, Geospatial AI platform for the City of Montgomery, Alabama. This application serves as a "Gov-Tech Urban Analyst," translating natural language intents into actionable geospatial insights, market gap analysis, and policy simulations.

---

## 🚀 Vision
Empower city planners with a data-driven "Copilot" that can detect ghost businesses, map retail gaps, simulate the revenue impact of zoning changes, and visualize municipal liability in real-time.

---

## 🛠️ Tech Stack
- **Dashboard**: [Streamlit](https://streamlit.io/) (Premium Dark-Themed UI)
- **Mapping**: [Folium](https://python-visualization.github.io/folium/) + [Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium)
- **AI Orchestration**: [LangGraph](https://www.langchain.com/langgraph) (Stateful Agent Workflows)
- **LLM Engine**: groq (Llama 3), OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet) with sequential fallback.
- **Geospatial Data**: ArcGIS Montgomery Open Data REST API
- **Web Intelligence**: Bright Data SERP Scraper (Real-time Business Verification)
- **Policy RAG**: ChromaDB (Vector Search) + Sentence-Transformers
- **Server**: FastMCP (Modern Server for AI Tools)
- **Mock Data**: Custom 311, Walkability, and Safety modules

---

## 🌟 Key Features

### 🕵️ 1. Ghost Business Detective
Identifies "Ghost Businesses"—entities registered in city property records but lacking a live web presence.
- **Visual**: Red markers with pulse animations.
- **Goal**: Highlight potential property tax liability and commercial vacancies.

### 🍔 2. Retail Gap & Market Demand
Analyze the distance between existing services (e.g., pharmacies, coffee) and vacant parcels.
- **Visual**: Catchment polygons and "Coffee/Retail" icons.
- **Goal**: Identify optimal sites for new businesses to solve "food/retail deserts."

### 💸 3. Liability & "Money Pit" Tracking
Cross-references city data with mock 311 reports to find high-maintenance "Money Pit" parcels.
- **Visual**: Intense pulse-red markers and cost breakdown bar charts.

### 📈 4. "Future-MGM" Simulator (2026 Rewrite)
Simulates a 20% property revenue lift across specific neighborhoods based on proposed code rewrites.
- **Visual**: Gradient pins and purple impact zone overlays.

### 🚶 5. The Yield Profile & Walkability
Calculates 15-minute city walkability scores and generates geospatial isochrone polygons.
- **Goal**: Measure the "yield" of a neighborhood in terms of accessibility.

### 📜 6. City Policy RAG
Ask natural language questions about the 1985 vs. 2026 Zoning Ordinances and Comprehensive Plans.
- **Example**: "What are the height standards for T4-O in North Montgomery?"

---

## 📁 Project Structure

```text
.
├── app.py                  # Main Streamlit Dashboard (UI & Map)
├── server.py               # FastMCP Server (Tool Registration)
├── requirements.txt        # Production-pinned dependencies
├── README.md               # You are here
├── scrape_cache.db         # Persistent cache for Bright Data scrapes
├── data_files/             # Knowledge base for Policy RAG
│   ├── comp_plan.pdf       # 2020 Comprehensive Plan
│   └── zoning.pdf          # Zoning Ordinances
├── docs/                   # Documentation for Business & Setup
│   ├── Project_Overview.md # High-level business overview
│   ├── Project_Workflow.md # Step-by-step logic and data flow
│   └── UI_User_Manual.md   # How to use the Streamlit application
└── src/
    ├── agent/              # LangGraph Orchestration & Logic
    │   ├── graph.py        # Central State Machine & Fallback logic
    │   ├── tools.py        # Functional wrappers for city tools
    │   └── prompts.py      # System personas & output protocols
    ├── api/                # External Data Integrations
    │   ├── arcgis/         # Montgomery ArcGIS Connectors
    │   │   ├── parcels.py  # Parcel & Valuation search
    │   │   └── zoning.py   # Point-in-polygon zoning check
    │   └── search/         # Live Web Intelligence
    │       └── brightdata.py 
    ├── rag/                # Legal & Policy Vector Search
    │   ├── engine.py       # ChromaDB Query / RAG logic
    │   └── indexer.py      # PDF -> Vector processing
    └── utils/              # Data simulations & helpers
        └── mock_data.py    # Mock 311, Isochrones, & Safety Buffers
```

---

## ⚙️ Installation & Setup

1. **Clone & Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **API Keys**: Create a `.env` file with the following:
   ```env
   GROQ_API_KEY=your_key
   OPENAI_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   BRIGHTDATA_API_KEY=your_key
   BRIGHTDATA_ZONE=your_zone
   ```

3. **Execution**:
   - **Start the Tool Server**: `uvicorn server:app --reload --port 8000`
   - **Launch the Center**: `streamlit run app.py`

---

## ⚖️ License
This project is licensed under the MIT License - see the `LICENSE` file for details.
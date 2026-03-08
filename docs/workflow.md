# 🛤️ Montgomery City Planner: Workflow & Architecture Diagram

This document illustrates the execution lifecycle of the Montgomery City Planner. It demonstrates how a user's natural language query is processed, orchestrated by the AI agent, and rendered on the geospatial dashboard.

## System Workflow Diagram

```mermaid
graph TD
    %% Define Styles
    classDef user fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff
    classDef ui fill:#0891b2,stroke:#06b6d4,stroke-width:2px,color:#fff
    classDef agent fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff
    classDef llm fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff
    classDef tools fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    classDef api fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    classDef output fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff

    %% Components
    User([\uD83D\uDC64 User Query/Intent]):::user
    
    subgraph Frontend [Streamlit Dashboard]
        UI[\uD83D\uDDA5\uFE0F Command Center Interface]:::ui
        ChatOut[\uD83D\uDCAC AI Copilot Feed]:::output
        MapOut[\uD83D\uDDFA\uFE0F Folium Living Map]:::output
    end
    
    subgraph Intelligence [AI Orchestration Layer]
        Agent[\uD83E\uDDE0 LangGraph State Machine]:::agent
        LLM[\uD83E\uDD16 LLM Backbone<br/>Groq/OpenAI/Anthropic]:::llm
    end

    subgraph DataServices [FastMCP Tool Server]
        ToolRouter[\uD83D\uDEE0\uFE0F Tool Execution Router]:::tools
        API_ArcGIS[\uD83C\uDF0D ArcGIS Montgomery REST]:::api
        API_Web[\uD83D\uDD0D Bright Data SERP API]:::api
        API_RAG[\uD83D\uDCDA ChromaDB RAG Engine]:::api
        API_Mock[\uD83D\uDCCA Utility & Mock Data]:::api
    end

    %% Flow
    User -->|Natural Language| UI
    UI -->|Session State| Agent
    Agent <-->|Context/Prompts| LLM
    LLM -->|Decision: Call Tool| ToolRouter
    
    ToolRouter -->|Parcels/Zoning| API_ArcGIS
    ToolRouter -->|Web Verification| API_Web
    ToolRouter -->|Policy Queries| API_RAG
    ToolRouter -->|311 & Walkability| API_Mock
    
    API_ArcGIS -.->|Geospatial Features| ToolRouter
    API_Web -.->|Live Search Snippets| ToolRouter
    API_RAG -.->|Vector Embeddings| ToolRouter
    API_Mock -.->|Simulated Metrics| ToolRouter
    
    ToolRouter -.->|Tool Output| Agent
    Agent -->|JSONDecoder Parsing| FinalProcessing{Extract Map & Chart JSON}
    
    FinalProcessing -->|Clean Markdown| ChatOut
    FinalProcessing -->|Polygons & Pins| MapOut
```

## Lifecycle Breakdown

1. **User Input**: A city planner enters a natural-language query into the Streamlit interface (e.g., "Find retail gaps in downtown").
2. **State Management**: LangGraph initializes an `AgentState` containing the conversation history.
3. **LLM Decisioning**: The core LLM (with Groq, OpenAI, and Anthropic fallback tiers) evaluates the prompt against available tools to decide the next action.
4. **Tool Execution**: 
   - Operations like `live_web_search_func` or `search_vacant_parcels_func` are routed to the FastMCP server.
   - The server queries external APIs (ArcGIS, Bright Data) or internal vectors (ChromaDB) and returns results.
5. **Data Synthesis**: The LLM synthesizes the results, summarizing them and constructing a strict `TRIGGER_MAP` or `CHART_DATA` JSON block.
6. **Rendering**:
   - The `app.py` script intercepts the payload.
   - A `JSONDecoder` cleanly strips the JSON map logic from the conversational output.
   - The user sees a professional text summary alongside a dynamically updated, interactive Folium map.

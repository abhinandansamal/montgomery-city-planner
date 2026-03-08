# 🛤️ Montgomery City Planner: Project Workflow Details

This document provides a comprehensive, step-by-step explanation of the Montgomery City Planner workflow. It outlines how a user's natural language question is processed by the AI orchestration layer, enriched with external municipal data, and finally presented as an actionable insight on the interactive dashboard.

---

## 🚦 1. User Input & Initialization

**The Entry Point**
The workflow begins when a user (e.g., a city planner, developer, or resident) opens the **Streamlit Command Center** (the dashboard). They type a natural-language query into the AI Copilot chat interface, such as:
> *"Find me the ghost businesses in downtown Montgomery."*

**State Management**
As the user hits submit, the system initializes an `AgentState`. This is a structured memory object (powered by LangGraph) that tracks:
- The history of the conversation (so the AI remembers context).
- The intermediate steps taken by the AI.
- The final outputs (like data tables or map triggers) that need to be sent back to the dashboard.

---

## 🧠 2. AI Orchestration & Decision Making

**The "Brain" of the Operation**
The user's query is sent to the core AI Orchestrator. The primary brain is powered by the Groq Llama 3 model (chosen for speed), but for resilience, the system features a built-in fallback sequence to OpenAI (GPT-4o) and Anthropic (Claude 3.5 Sonnet) if rate limits are hit.

**Reasoning step (ReAct Pattern)**
The AI does not guess the answer. It reads the system's "prompt instructions" and realizes that to find "ghost businesses in downtown," it needs real data. It determines which of its integrated tools is best suited for the job.

---

## 🛠️ 3. Data Retrieval & Tool Execution

The AI selects a specific tool and dispatches a request to the **FastMCP Tool Server**. The server acts as a secure bridge between the AI and the outside world. Depending on the query, it reaches out to different data sources:

**Scenario A: Live API Lookups (ArcGIS)**
If the AI needs property data, it calls the ArcGIS Montgomery Open Data REST API. It fetches real-world parcels, land values, and owner names based on the user's location parameters.

**Scenario B: Live Web Intelligence (Bright Data)**
To verify if a business physically exists, the AI triggers a Bright Data scraper. This performs a live Google Search Engine Results Page (SERP) query to check if the registered property owner has an active website or business listing.

**Scenario C: Policy Analysis (ChromaDB RAG)**
If the user asks a legal zoning question, the AI queries the ChromaDB Vector Database, which searches through the vectorized 2020 Comprehensive Plan and Zoning Ordinances to find the exact legal clause.

**Scenario D: Simulated Metrics (Mock Data)**
For advanced features like 311 liability costs or 15-minute walkability distances, the system relies on custom utility modules that generate mathematically accurate, simulated geospatial features overlaid on the real map.

---

## 🧩 4. Data Synthesis & JSON Construction

Once the FastMCP server returns the raw data from the various sources, the AI Orchestrator receives the information.

**Cross-Referencing**
The AI synthesizes the data. For instance, in our Ghost Business example, it compares the official ArcGIS list of business owners against the bright data web search results. If it finds a mismatch (official record exists, but no live web presence), it flags it as a "Ghost Business."

**Trigger Generation**
The AI writes out its final analysis in plain English. More importantly, it generates a strict JSON payload (like `<TRIGGER_MAP>`) containing the exact latitude, longitude, color, and icon for the map marker.

---

## 🖥️ 5. Final Presentation & Map Rendering

**The Cleanup Phase**
Before the final message is shown to the user, the Streamlit dashboard intercepts the AI's response. A custom `json.JSONDecoder` pipeline scans the text, perfectly extracts the complex JSON mapping data, and completely removes it from the text. 

**The Output**
1. **The Chat Feed**: The user receives a clean, professional written summary of the findings (e.g., "I found 8 ghost businesses in downtown..."). No broken code or messy data is visible in the chat.
2. **The Living Map**: Simultaneously, the extracted JSON data is sent to the Folium map engine. The interactive map instantaneously updates, dropping animated pins or drawing colored zones exactly where the AI targeted them.

---
*End of Workflow*

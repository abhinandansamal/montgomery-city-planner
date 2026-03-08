# 🖥️ Montgomery City Planner: UI User Manual

Welcome to the **Montgomery City Planner Command Center**. This manual will guide you through the features and functionalities of the user interface (UI), helping you easily navigate the dashboard and interact with the AI Copilot.

---

## 🧭 The Dashboard Layout

The Command Center is divided into three main sections:

1. **The Navigation Sidebar (Left)**
2. **The AI Copilot Chat (Middle)**
3. **The Living Map (Right)**

---

## 1️⃣ The Navigation Sidebar (Left Panel)

This panel contains your overarching controls and displays high-level statistics about your current session.

*   **Command Center Title & Logo:** Confirms you are in the Montgomery City Planner dashboard.
*   **Zoning Simulation Toggle:**
    *   **Slider:** A toggle switch that lets you instantly switch the map context between the *Current (1985)* zoning rules and the proposed *Future (2026)* rules.
    *   **Current Selection Display:** A small box below the slider confirms which zoning year you are currently viewing.
*   **Session Stats:** A live scoreboard of your current activity:
    *   **Map Pins:** The total number of locations currently flagged on your map.
    *   **Ghosts:** The number of "Ghost Businesses" identified in your current query.
    *   **Vacant:** The number of vacant parcels found.
    *   **Queries:** How many questions you have asked the AI in this session.
*   **Settings / Clear Data:** Options to clear your current map and chat history to start a fresh analysis.

---

## 2️⃣ The AI Copilot Chat (Middle Panel)

This is where you talk to the AI, ask questions, and read its reports.

*   **Chat History:** The large scrolling area displays the conversation. Your questions appear on the right, and the AI's detailed answers (along with any data tables or charts) appear on the left.
*   **Message Input Box:** Located at the bottom of the chat panel. Click here, type your question in plain English (e.g., *"Show me vacant lots near downtown"*), and press **Enter** to submit.
*   **"Thinking" Indicator:** When you submit a question, a spinner will appear while the AI fetches data from the city records and live web.
*   **Clean Output:** The AI automatically formats its answers into easy-to-read text, bullet points, and charts. It handles all the complex data behind the scenes so your view remains clean and professional.

---

## 3️⃣ The Living Map (Right Panel)

The Living Map is the visual heartbeat of the application. It dynamically updates based on your conversations with the AI Copilot.

*   **Interactive Controls:**
    *   **Zoom In/Out:** Use the `+` and `-` buttons in the top left corner.
    *   **Pan:** Click and drag anywhere on the map to move around Montgomery.
*   **Dynamic Markers (Pins):** When you ask for map-related data, the AI drops pins onto the map:
    *   **🔴 Red Pins:** Flag liabilities like Ghost Businesses or high-maintenance "Money Pits."
    *   **🟣 Purple/Gradient Pins:** Show predicted impact zones for 2026 rezoning.
    *   **Icons:** Pins often contain small icons (like an 'x' or a building) for precise identification.
*   **Polygons (Colored Zones):**
    *   **Walkability/Isochrones:** Colored shapes that show how far a pedestrian can walk in 15 minutes.
    *   **Retail Gaps/Catchments:** Yellow or transparent shapes identifying zones that are missing specific services (like retail or food).
*   **Map Legend:** Located below the map, this provides a quick reference key so you know what the different colors and shapes represent.

---

## 💡 Quick Start Example

Want to see it in action? Try this workflow:

1.  Look at the **Message Input Box** at the bottom of the middle panel.
2.  Type: *"Find ghost businesses in downtown."*
3.  Press **Enter**.
4.  Watch the **AI Copilot** think and then provide a summary report.
5.  Look at the **Living Map** on the right to see the exact red pins indicating where those properties are located.
6.  Check your **Session Stats** on the left to see the numbers automatically update!

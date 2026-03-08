"""Montgomery City Planner — Streamlit Command Center.

A 30/70 split-screen layout with an AI Copilot chat feed (left)
and a Living Map (right) powered by Folium. Includes a sidebar
with Zoning Simulation controls and dynamic map pin rendering.
"""

import asyncio
import json
import re

import folium
import streamlit as st
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Montgomery City Planner",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Command Center Aesthetic
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import premium font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Root variables */
    :root {
        --bg-primary: #f0f4f8;
        --bg-secondary: #e2e8f0;
        --bg-card: #ffffff;
        --bg-card-hover: #f1f5f9;
        --accent-blue: #2563eb;
        --accent-cyan: #0891b2;
        --accent-emerald: #059669;
        --accent-purple: #7c3aed;
        --accent-amber: #d97706;
        --accent-red: #dc2626;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --border-subtle: rgba(0, 0, 0, 0.08);
        --glow-blue: rgba(37, 99, 235, 0.1);
        --glow-cyan: rgba(8, 145, 178, 0.1);
    }

    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e8eef5 50%, #f0f4f8 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }

    /* Hide default Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Header bar */
    .command-header {
        background: linear-gradient(135deg, #1e3a5f, #1a5276);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(30, 58, 95, 0.25);
    }

    .command-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }

    .command-header .subtitle {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.85rem;
        font-weight: 400;
        margin-top: 4px;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-online {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    }

    /* Panel styles */
    .chat-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        height: 72vh;
        overflow-y: auto;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
    }

    .chat-panel::-webkit-scrollbar {
        width: 4px;
    }

    .chat-panel::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }

    .panel-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #0891b2;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
    }

    .map-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
    }

    /* Chat messages */
    .user-msg {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 14px 18px;
        margin: 10px 0;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1e293b;
    }

    .ai-msg {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 14px;
        padding: 14px 18px;
        margin: 10px 0;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #1e293b;
    }

    .thought-trace {
        background: #f5f3ff;
        border-left: 3px solid #7c3aed;
        border-radius: 0 10px 10px 0;
        padding: 10px 14px;
        margin: 8px 0;
        font-size: 0.8rem;
        color: #475569;
        font-style: italic;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f, #1a365d) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    /* Slider styling */
    .stSlider > div > div {
        background: rgba(255, 255, 255, 0.15) !important;
    }

    /* Yield gauge placeholder */
    .yield-gauge {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
        text-align: center;
    }

    .yield-score {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .yield-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    /* Revenue lift badge */
    .revenue-lift {
        display: inline-block;
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        margin: 6px 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* ===== CHAT INPUT — force white bg and dark text everywhere ===== */
    .stChatInput,
    .stChatInput > div,
    .stChatInput > div > div,
    .stChatInput div,
    .stChatInput form,
    .stChatInput [data-testid],
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] div,
    [data-testid="stChatInputTextArea"],
    [data-testid="stChatInputTextArea"] > div,
    .stChatInput div[data-baseweb],
    .stChatInput div[data-baseweb] > div {
        background: #ffffff !important;
        background-color: #ffffff !important;
        border-color: #93c5fd !important;
    }

    .stChatInput textarea,
    [data-testid="stChatInputTextArea"] textarea,
    .stChatInput input,
    .stChatInput div[contenteditable],
    .stChatInput [role="textbox"] {
        color: #1e293b !important;
        background: #ffffff !important;
        background-color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        caret-color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
    }

    .stChatInput textarea::placeholder,
    [data-testid="stChatInputTextArea"] textarea::placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
    }

    .stChatInput button {
        background: #2563eb !important;
        color: #ffffff !important;
    }

    /* ===== Force light backgrounds inside Streamlit containers ===== */
    .stContainer, [data-testid="stVerticalBlock"],
    .element-container, .stMarkdown,
    [data-testid="stChatMessage"],
    [data-testid="stExpander"] {
        color: #1e293b !important;
    }

    /* Fix inner containers that Streamlit renders with dark backgrounds */
    div[data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stChatMessage"],
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        color: #1e293b !important;
    }

    /* Ensure chart containers are visible */
    .stVegaLiteChart, .stBarChart {
        background-color: #ffffff !important;
        padding: 10px;
        border-radius: 8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stChatMessage"] > div {
        background-color: #ffffff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div {
        background-color: #ffffff !important;
    }

    /* Chat message text must be dark */
    .stChatMessage, .stChatMessage p, .stChatMessage span,
    .stChatMessage div, .stChatMessage li, .stChatMessage a,
    [data-testid="stChatMessage"], [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {
        color: #1e293b !important;
        background-color: transparent !important;
    }

    .stChatMessage code {
        background: #f1f5f9 !important;
        color: #334155 !important;
    }

    /* Markdown text inside main area */
    .main .stMarkdown, .main .stMarkdown p,
    .main .stMarkdown span, .main .stMarkdown div,
    .main .stMarkdown li, .main .stMarkdown a,
    .main .stMarkdown h1, .main .stMarkdown h2,
    .main .stMarkdown h3, .main .stMarkdown h4 {
        color: #1e293b !important;
    }

    /* Thought trace messages */
    .thought-trace {
        color: #475569 !important;
    }

    /* Bottom chat input container */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] div {
        background: transparent !important;
    }

    /* Stats cards */
    .stat-card {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 14px 16px;
        margin: 6px 0;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        background: rgba(255, 255, 255, 0.18);
        border-color: rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #93c5fd;
    }

    .stat-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.65);
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Zoning badge */
    .zoning-badge-current {
        background: rgba(251, 191, 36, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.35);
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .zoning-badge-2026 {
        background: rgba(52, 211, 153, 0.2);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.35);
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Map Pin Animations */
    @keyframes pulse-ring {
        0% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(220, 38, 38, 0); }
        100% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }
    .pulse-marker {
        animation: pulse-ring 2s infinite cubic-bezier(0.66, 0, 0, 1);
    }
    
    @keyframes bounce-up {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-15px); }
    }
    .bounce-marker {
        animation: bounce-up 1s infinite ease-in-out;
    }
    
    @keyframes blink-glow {
        0%, 100% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.5); border-color: white; }
        50% { box-shadow: 0 0 20px #10b981, inset 0 0 10px #10b981; border-color: #10b981; }
    }
    .blink-marker {
        animation: blink-glow 1.5s infinite;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "map_pins" not in st.session_state:
    st.session_state.map_pins = []
if "map_polygons" not in st.session_state:
    st.session_state.map_polygons = []
if "map_lines" not in st.session_state:
    st.session_state.map_lines = []
if "map_center" not in st.session_state:
    st.session_state.map_center = [32.3668, -86.3000]  # Montgomery, AL
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 12
if "thought_traces" not in st.session_state:
    st.session_state.thought_traces = []
if "yield_data" not in st.session_state:
    st.session_state.yield_data = None
if "zoning_mode" not in st.session_state:
    st.session_state.zoning_mode = "Current (1985)"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
import re

def extract_json_block(text: str, marker: str) -> tuple[dict | None, str]:
    """Find a JSON block starting with marker, return (dict, cleaned_text).
    
    Supports multiple formats: 
    - MARKER: { ... }
    - <MARKER> { ... }
    - MARKER { ... }
    """
    # Regex to find the marker start flexibly
    marker_pattern = rf"(?:<{marker}>|{marker}\s*:|{marker})"
    match = re.search(marker_pattern, text)
    if not match:
        return None, text
        
    start_index = match.start()
    search_from = match.end()
    
    # Look for the first '{' after the marker
    first_brace = text.find("{", search_from)
    if first_brace == -1:
        # If no brace after marker, check if the marker itself is followed by JSON directly
        # (Though regex usually covers this, being safe)
        return None, text
        
    try:
        # Use JSONDecoder to find the next complete JSON object
        decoder = json.JSONDecoder()
        obj, end_index = decoder.raw_decode(text[first_brace:])
        
        # Calculate indices for cleaning
        actual_end = first_brace + end_index
        
        # Look ahead for closing tags/markdown blocks to include in cleaning
        clean_end = actual_end
        peek_ahead = text[actual_end:actual_end+50]
        
        # Check for markdown codes or closing XML-style tags
        if "```" in peek_ahead:
            clean_end = actual_end + peek_ahead.find("```") + 3
        elif f"</{marker}>" in peek_ahead:
            clean_end = actual_end + peek_ahead.find(f"</{marker}>") + len(marker) + 3
            
        cleaned_text = text[:start_index] + text[clean_end:]
        return obj, cleaned_text
    except Exception:
        return None, text


def parse_trigger_map(response_text: str) -> dict | None:
    """Extract TRIGGER_MAP JSON."""
    obj, _ = extract_json_block(response_text, "TRIGGER_MAP")
    return obj


def parse_chart_data(response_text: str) -> dict | None:
    """Extract CHART_DATA JSON."""
    obj, _ = extract_json_block(response_text, "CHART_DATA")
    return obj


def clean_response(text: str) -> str:
    """Remove TRIGGER_MAP and CHART_DATA blocks from display text iteratively."""
    # Remove all instances of TRIGGER_MAP and CHART_DATA
    current_text = text
    while True:
        _, new_text = extract_json_block(current_text, "TRIGGER_MAP")
        if new_text == current_text:
            break
        current_text = new_text
        
    while True:
        _, new_text = extract_json_block(current_text, "CHART_DATA")
        if new_text == current_text:
            break
        current_text = new_text

    # Optional: If Pitch Deck, add a generative image placeholder
    if "# 📊 Concept Pitch Deck" in current_text and "![Concept]" not in current_text:
        current_text += "\n\n![Concept](https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=800&h=600)"
    
    return current_text.strip()


def get_pin_icon_color(color: str) -> str:
    """Map semantic color names to Folium icon colors.

    Args:
        color: Semantic color (red, green, yellow, grey, etc.).

    Returns:
        Folium-compatible color string.
    """
    color_map = {
        "red": "red",
        "dark_red": "darkred",
        "darkred": "darkred",
        "green": "green",
        "yellow": "orange",
        "grey": "gray",
        "gray": "gray",
        "purple": "purple",
        "blue": "blue",
    }
    return color_map.get(color.lower(), "blue")


def create_map() -> folium.Map:
    """Build a Folium map centered on Montgomery with current pins.

    Returns:
        A Folium Map object with all active pins drawn.
    """
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles="OpenStreetMap",
    )

    # Add Polygons
    for poly in st.session_state.map_polygons:
        coords = poly.get("coords", [])
        if coords:
            folium.Polygon(
                locations=coords,
                color=poly.get("color", "#3388ff"),
                fill=True,
                fill_color=poly.get("color", "#3388ff"),
                fill_opacity=poly.get("fill_opacity", 0.4),
                weight=2
            ).add_to(m)

    # Add Lines
    for line in st.session_state.map_lines:
        coords = line.get("coords", [])
        if coords:
            folium.PolyLine(
                locations=coords,
                color=line.get("color", "#3388ff"),
                weight=4,
                opacity=0.8
            ).add_to(m)

    # Add pins
    for pin in st.session_state.map_pins:
        color = get_pin_icon_color(pin.get("color", "blue"))
        label = pin.get("label", "")
        pin_type = pin.get("type", "")
        animation = pin.get("animation", None)
        icon_name = pin.get("icon", "info-sign")  # Allow overriding icon from agent

        # Determine default fallback icon if none provided
        if icon_name == "info-sign":
            if pin_type == "ghost_business" or color == "red":
                icon_name = "remove-sign"
            elif pin_type == "retail_desert" or color in ("green", "orange"):
                icon_name = "shopping-cart"
            elif pin_type == "money_pit" or color == "darkred":
                icon_name = "warning-sign"
            elif pin_type == "vacant" or color == "gray":
                icon_name = "unchecked"
            elif pin.get("icon") == "hazard":
                icon_name = "exclamation-sign"

        popup_html = f"""
        <div style="font-family: Inter, sans-serif; min-width: 200px;">
            <b style="color: #1a1f35;">{label}</b><br>
            <small style="color: #64748b;">Type: {pin_type}</small><br>
            <small style="color: #64748b;">({pin['lat']:.4f}, {pin['lon']:.4f})</small>
        </div>
        """

        # Custom animated icons via DivIcon
        if animation:
            css_class = ""
            if animation == "bounce":
                css_class = "bounce-marker"
            elif animation == "pulse" or color == "darkred":
                css_class = "pulse-marker"
            elif color == "blinking_green":
                css_class = "blink-marker"
                
            # A completely custom HTML marker for animations
            html = f"""
            <div style="
                width: 24px; height: 24px; 
                background-color: {color if color != 'blinking_green' else '#10b981'};
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            " class="{css_class}"></div>
            """
            
            folium.Marker(
                location=[pin["lat"], pin["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=label,
                icon=folium.DivIcon(html=html)
            ).add_to(m)
        else:
            # Standard Folium Icon
            folium.Marker(
                location=[pin["lat"], pin["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=label,
                icon=folium.Icon(color=color, icon=icon_name, prefix="glyphicon" if "-" in icon_name else "fa"),
            ).add_to(m)

    # 2026 Zoning overlay (purple impact areas)
    if st.session_state.zoning_mode == "2026 Rewrite":
        for pin in st.session_state.map_pins:
            folium.CircleMarker(
                location=[pin["lat"], pin["lon"]],
                radius=25,
                color="#8b5cf6",
                fill=True,
                fill_color="#8b5cf6",
                fill_opacity=0.15,
                weight=1,
            ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Sidebar — Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 16px 0;">
        <div style="font-size: 2.2rem;">🏙️</div>
        <h2 style="margin: 8px 0 4px 0; font-weight: 800; color: #ffffff;">
            Command Center
        </h2>
        <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">Montgomery City Planner</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Zoning Simulation Slider
    st.markdown("### 🔧 Zoning Simulation")
    zoning_option = st.select_slider(
        "Zoning Code",
        options=["Current (1985)", "2026 Rewrite"],
        value=st.session_state.zoning_mode,
        key="zoning_slider",
    )
    st.session_state.zoning_mode = zoning_option

    if zoning_option == "2026 Rewrite":
        st.markdown(
            '<div class="revenue-lift">📈 2026 Code Revenue Lift: +18-25%</div>',
            unsafe_allow_html=True,
        )
        st.info("Property values recalculated with 2026 zoning uplift assumptions.")
    else:
        st.markdown(
            '<span class="zoning-badge-current">📋 Current 1985 Zoning</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Stats Dashboard
    st.markdown("### 📊 Session Stats")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(st.session_state.map_pins)}</div>
            <div class="stat-label">Map Pins</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        # Count by color 'red' (case-insensitive)
        ghost_count = len([p for p in st.session_state.map_pins if p.get("color", "").lower() == "red"])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #fca5a5;">{ghost_count}</div>
            <div class="stat-label">Ghosts</div>
        </div>
        """, unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        # Count by color 'black' or 'grey' (case-insensitive)
        vacant_count = len([p for p in st.session_state.map_pins if p.get("color", "").lower() in ["black", "grey"]])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #d1d5db;">{vacant_count}</div>
            <div class="stat-label">Vacant</div>
        </div>
        """, unsafe_allow_html=True)
    with col_d:
        query_count = (len(st.session_state.messages) // 2) if st.session_state.messages else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #6ee7b7;">{query_count}</div>
            <div class="stat-label">Queries</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Yield Gauge
    st.markdown("### 📈 Yield Gauge")
    if st.session_state.yield_data:
        yd = st.session_state.yield_data
        st.markdown(f"""
        <div class="yield-gauge">
            <div class="yield-score">{yd.get('score', 'N/A')}</div>
            <div class="yield-label">Yield Score</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="yield-gauge" style="opacity: 0.5;">
            <div class="yield-score">—</div>
            <div class="yield-label">Query a parcel to see its yield</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Clear / Reset
    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.map_pins = []
        st.session_state.thought_traces = []
        st.session_state.yield_data = None
        st.session_state.map_center = [32.3668, -86.3000]
        st.session_state.map_zoom = 12
        st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="command-header">
    <div>
        <h1>🏙️ The Montgomery City Planner</h1>
        <div class="subtitle">Generative Planning • Ghost Detection • Yield Optimization</div>
    </div>
    <div class="status-badge status-online">
        <div class="pulse-dot"></div>
        System Online
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main Layout — 30/70 Split
# ---------------------------------------------------------------------------
chat_col, map_col = st.columns([3, 7], gap="medium")

# ---- LEFT: AI Copilot Chat ----
with chat_col:
    st.markdown('<div class="panel-title">🤖 AI Copilot</div>', unsafe_allow_html=True)

    # Chat message display
    chat_container = st.container(height=600)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px; color: #64748b;">
                <div style="font-size: 3rem; margin-bottom: 12px;">🔍</div>
                <div style="font-size: 0.95rem; font-weight: 600; color: #334155;">
                    Welcome, City Planner
                </div>
                <div style="font-size: 0.8rem; margin-top: 8px; line-height: 1.6; color: #64748b;">
                    Try asking:<br>
                    <em>"Show me ghost businesses in downtown"</em><br>
                    <em>"Find retail deserts for pharmacies"</em><br>
                    <em>"What are the biggest money pits?"</em><br>
                    <em>"Show clean slate parcels near I-85"</em>
                </div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(content)
            elif role == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    # Check for Yield Profile Comparison to wrap in columns
                    if "### Comparison Grid" in content:
                        parts = content.split("### Comparison Grid")
                        st.markdown(clean_response(parts[0]))
                        
                        st.markdown("### ⚖️ Strategic Comparison")
                        cols = st.columns(2)
                        grid_lines = parts[1].strip().split('\n')
                        
                        # Very simple heuristic: split the bullet points between the columns
                        col1_text, col2_text = "", ""
                        target = 1
                        for line in grid_lines:
                            if "**Parcel B**" in line or "**Option 2**" in line or "**Site 2**" in line:
                                target = 2
                            
                            if target == 1:
                                col1_text += line + "\n"
                            else:
                                col2_text += line + "\n"
                                
                        with cols[0]:
                            st.info(col1_text)
                        with cols[1]:
                            st.success(col2_text)
                    else:
                        st.markdown(clean_response(content))
                        
                    # Check for Pitch Deck
                    if "# 📊 Concept Pitch Deck" in content:
                        st.download_button(
                            label="📥 Download Pitch Deck (PDF/Markdown)",
                            data=clean_response(content),
                            file_name="concept_pitch_deck.md",
                            mime="text/markdown",
                        )
            elif role == "thought":
                st.markdown(
                    f'<div class="thought-trace">🧠 {content}</div>',
                    unsafe_allow_html=True,
                )
            elif role == "chart":
                # Render chart data
                with st.chat_message("assistant", avatar="📊"):
                    title = content.get("title", "Data Visualization")
                    st.markdown(f"**{title}**")
                    # Try 'data' key first, then use the whole content if it has no 'data' key
                    chart_vals = content.get("data")
                    if not chart_vals and content:
                        # Maybe the whole thing is the data
                        chart_vals = {k: v for k, v in content.items() if k not in ["type", "title"]}
                    
                    if chart_vals:
                        st.bar_chart(chart_vals)
                    else:
                        st.warning("No chart data available to plot.")

    # Chat input
    user_input = st.chat_input("Ask the City Planner...", key="chat_input")

    if user_input:
        # Clear previous map state for the new query
        st.session_state.map_pins = []
        st.session_state.map_polygons = []
        st.session_state.map_lines = []
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Show thinking indicator
        st.session_state.messages.append({
            "role": "thought",
            "content": f"Analyzing query: '{user_input}' — Routing to tools...",
        })

        # Run the agent
        try:
            from src.agent.graph import run_agent

            with st.spinner("🔍 Investigating..."):
                result = asyncio.run(run_agent(user_input))

            response_text = result.get("response", "I couldn't process that query.")
            map_triggers = result.get("map_triggers", {})
            thought_traces = result.get("thought_traces", [])

            # Add actual tool traces
            for trace in thought_traces:
                st.session_state.messages.append({
                    "role": "thought",
                    "content": trace,
                })

            # Parse TRIGGER_MAP from response if not in state
            if not map_triggers:
                map_triggers = parse_trigger_map(response_text) or {}
                
            chart_data = parse_chart_data(response_text)

            # Update map pins and shapes
            if map_triggers:
                if "pins" in map_triggers:
                    new_pins = map_triggers["pins"]
                    pin_type = map_triggers.get("type", "unknown")
                    for pin in new_pins:
                        pin["type"] = pin.get("type", pin_type)
                    st.session_state.map_pins.extend(new_pins)

                    # Pan to first new pin
                    if new_pins:
                        st.session_state.map_center = [
                            new_pins[0]["lat"],
                            new_pins[0]["lon"],
                        ]
                        st.session_state.map_zoom = 14
                        
                # Store polygons and lines for rendering
                if "polygons" in map_triggers:
                    st.session_state.map_polygons = st.session_state.get("map_polygons", []) + map_triggers["polygons"]
                if "lines" in map_triggers:
                    st.session_state.map_lines = st.session_state.get("map_lines", []) + map_triggers["lines"]

            # Add AI response text (cleaned)
            st.session_state.messages.append({
                "role": "assistant",
                "content": clean_response(response_text),
            })
            
            # Store chart if generated
            if chart_data:
                st.session_state.messages.append({
                    "role": "chart",
                    "content": chart_data,
                })

        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
            })

        st.rerun()


# ---- RIGHT: Living Map ----
with map_col:
    st.markdown('<div class="panel-title">🗺️ Living Map</div>', unsafe_allow_html=True)

    # Build and render map
    city_map = create_map()
    st_folium(
        city_map,
        width=None,
        height=550,
        returned_objects=[],
    )

    # Map legend
    st.markdown("""
    <div style="display: flex; gap: 16px; padding: 12px 18px;
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
                margin-top: 8px; flex-wrap: wrap;">
        <span style="font-size: 0.75rem; color: #475569;">
            🔴 <span style="color: #dc2626;">Ghost Business</span>
        </span>
        <span style="font-size: 0.75rem; color: #475569;">
            🟡 <span style="color: #d97706;">Retail Desert</span>
        </span>
        <span style="font-size: 0.75rem; color: #475569;">
            🟢 <span style="color: #059669;">Recommended Site</span>
        </span>
        <span style="font-size: 0.75rem; color: #475569;">
            ⚫ <span style="color: #6b7280;">Vacant Parcel</span>
        </span>
        <span style="font-size: 0.75rem; color: #475569;">
            🟣 <span style="color: #7c3aed;">2026 Impact Zone</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

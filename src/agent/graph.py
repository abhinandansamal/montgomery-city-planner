"""LangGraph agent orchestration for The Montgomery Yield Matchmaker.

This module defines the AgentState, state machine nodes, tool routing loop,
and provides the high-level run_agent API for the application.
"""

import json
import os
import re
from typing import Annotated, Any, Dict, List, TypedDict, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import TOOLS

# Load environment variables
load_dotenv(override=True)


class AgentState(TypedDict):
    """Represents the state of the agent in the LangGraph.

    Attributes:
        messages (List[BaseMessage]): Annotated list of messages with add_messages logic.
        target_neighborhood (str): Optional context for the current neighborhood.
        map_triggers (Dict[str, Any]): Extracted map-related actions from the LLM.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    target_neighborhood: str
    map_triggers: Dict[str, Any]


def _get_llm():
    """Create and return the LLM instance with tools and fallback chain bound.
    
    Attempts to use Groq (Llama 3), then falls back to OpenAI (GPT-4o)
    and Anthropic (Claude-3-Haiku) in case of rate limits or failures.

    Returns:
        The configured LLM runnable with fallbacks.
    """
    llm_groq = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY", ""),
    ).bind_tools(TOOLS)
    
    llm_openai = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    ).bind_tools(TOOLS)
    
    llm_anthropic = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.3,
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    ).bind_tools(TOOLS)
    
    # Sequence of fallbacks
    return llm_groq.with_fallbacks([llm_openai, llm_anthropic])


def call_model(state: AgentState) -> Dict[str, Any]:
    """Invoke the LLM with the current message history.

    Args:
        state: Current agent state.

    Returns:
        A dictionary containing the new AIMessage to append to the state.
    """
    llm = _get_llm()
    messages = state["messages"]

    # Prepend system prompt if history is empty or first message isn't System
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    # Context window protection: truncate massive tool outputs
    processed_messages = []
    for msg in messages:
        if getattr(msg, "type", "") == "tool" and isinstance(msg.content, str):
            if len(msg.content) > 4000:
                from langchain_core.messages import ToolMessage
                msg = ToolMessage(
                    content=msg.content[:4000] + "\n\n...[DATA TRUNCATED]...", 
                    tool_call_id=msg.tool_call_id, 
                    name=msg.name
                )
        processed_messages.append(msg)

    response = llm.invoke(processed_messages)
    return {"messages": [response]}


def extract_map_triggers(state: AgentState) -> Dict[str, Any]:
    """Parse TRIGGER_MAP from the last AI message and store in state.

    Handles markdown code blocks and whitespace variations.
    Uses JSONDecoder to robustly handle nested braces.

    Args:
        state: Current agent state.

    Returns:
        A dictionary with the extracted map_triggers.
    """
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, AIMessage):
        return {"map_triggers": {}}

    content = last_msg.content
    marker = "TRIGGER_MAP"
    
    # Flexible marker pattern: <TRIGGER_MAP>, TRIGGER_MAP: or TRIGGER_MAP
    marker_pattern = rf"(?:<{marker}>|{marker}\s*:|{marker})"
    match = re.search(marker_pattern, content)
    if not match:
        return {"map_triggers": {}}
        
    search_from = match.end()
    
    # Look for the first '{' after the marker
    first_brace = content.find("{", search_from)
    if first_brace == -1:
        return {"map_triggers": {}}
        
    try:
        # Use JSONDecoder to find the next complete JSON object
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(content[first_brace:])
        return {"map_triggers": obj}
    except Exception:
        return {"map_triggers": {}}


def should_continue(state: AgentState) -> str:
    """Decide whether the agent should call tools or move to extraction.

    Args:
        state: Current agent state.

    Returns:
        'tools' if the last message has tool calls, 'extract' otherwise.
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "extract"


def build_agent_graph() -> StateGraph:
    """Construct the LangGraph agent with Think-Act-Observe loop.

    Returns:
        A compiled StateGraph ready for invocation.
    """
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_node("extract", extract_map_triggers)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "extract": "extract"},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("extract", END)

    return graph.compile()


# --- Public Entry Points ---

_agent = None

def get_agent():
    """Return the singleton compiled agent graph."""
    global _agent
    if _agent is None:
        _agent = build_agent_graph()
    return _agent


async def run_agent(query: str, neighborhood: str = "") -> Dict[str, Any]:
    """Run the agent with a user query and return response + map triggers.

    Args:
        query: The user's natural-language query.
        neighborhood: Optional target neighborhood context.

    Returns:
        A dictionary containing:
            - response (str): The final AI text.
            - map_triggers (dict): Geographic actions for the map.
            - thought_traces (list): Summary of tools used.
    """
    agent = get_agent()
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "target_neighborhood": neighborhood,
        "map_triggers": {},
    }

    result = await agent.ainvoke(initial_state)

    response_text = ""
    thought_traces = []
    
    # Extract thought traces from tool calls
    for msg in result["messages"]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                args_str = ", ".join(f"{k}={v}" for k, v in tc.get("args", {}).items())
                thought_traces.append(f"🛠️ **Using Tool:** `{tc['name']}({args_str})`")

    # Final text is the last contentful AIMessage
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            break

    return {
        "response": response_text,
        "map_triggers": result.get("map_triggers", {}),
        "thought_traces": thought_traces,
    }

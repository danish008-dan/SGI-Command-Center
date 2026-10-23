# ai/hod_graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

from ai.hod_gateway import get_hod_llm
from ai.hod_tools import HOD_READ_TOOLS, HOD_EXECUTE_TOOLS


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    intent: str
    sender: str


llm = get_hod_llm()

# Combine all tools for the Supervisor to choose from
ALL_HOD_TOOLS = HOD_READ_TOOLS + HOD_EXECUTE_TOOLS

# --- Logical Agents ---
supervisor_agent = llm.bind_tools(ALL_HOD_TOOLS)

MULTILINGUAL_RULES = """
CRITICAL RULES FOR RESPONSE GENERATION:
1. LANGUAGE MATCHING: Respond in the EXACT SAME language the HOD used (English, Hindi, Hinglish, Gujarati).
2. DATA INTEGRITY: DO NOT translate authoritative database values (names, IDs, statuses).
3. NO HALLUCINATION: If a tool returns an error, inform the HOD honestly. NEVER guess data.
4. ACTION SAFETY: For execute actions, clearly state what will happen and ask for confirmation. If an action fails, report it accurately without claiming success.
"""


def supervisor_node(state):
    system_prompt = SystemMessage(content=f"""You are the HOD AI Supervisor. 
    Analyze the HOD's request and determine the intent or call the appropriate tool.
    - For overview, attendance, workload, or pending approvals: Route to Academic Agent.
    - For creating notices, events, meetings, or maintenance requests: Route to Operations Agent.
    Reply with the intent keyword or call the tool directly.
    {MULTILINGUAL_RULES}""")

    response = supervisor_agent.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "sender": "Supervisor"}


def academic_node(state):
    sys = SystemMessage(
        content=f"You are the Academic Agent for the HOD. Use tools to fetch academic data. {MULTILINGUAL_RULES}")
    # Academic agent only has read access
    academic_llm = llm.bind_tools(HOD_READ_TOOLS)
    res = academic_llm.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Academic Agent"}


def operations_node(state):
    sys = SystemMessage(
        content=f"You are the Operations Agent for the HOD. Use tools to create department notices, events, meetings, or maintenance requests. {MULTILINGUAL_RULES}")
    operations_llm = llm.bind_tools(HOD_EXECUTE_TOOLS)
    res = operations_llm.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Operations Agent"}


# --- Build Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Academic Agent", academic_node)
workflow.add_node("Operations Agent", operations_node)
workflow.add_node("Tools", ToolNode(ALL_HOD_TOOLS))


def route_from_supervisor(state):
    last_msg = state["messages"][-1].content.lower()
    if "notice" in last_msg or "event" in last_msg or "meeting" in last_msg or "maintenance" in last_msg:
        return "Operations Agent"
    return "Academic Agent"


workflow.set_entry_point("Supervisor")
workflow.add_conditional_edges("Supervisor", route_from_supervisor, {
    "Operations Agent": "Operations Agent",
    "Academic Agent": "Academic Agent"
})

# If agents call a tool, route to tools node. If not, route to END.
workflow.add_conditional_edges("Academic Agent", lambda state: "Tools" if state["messages"][-1].tool_calls else END)
workflow.add_conditional_edges("Operations Agent", lambda state: "Tools" if state["messages"][-1].tool_calls else END)

# Route back from tools to the respective agent that called it
workflow.add_edge("Tools", "Supervisor")

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
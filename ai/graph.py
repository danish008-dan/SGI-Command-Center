# ai/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

from ai.gateway import get_llm
from ai.tools import (
    ACADEMIC_TOOLS, FINANCE_TOOLS, HR_TOOLS,
    CAMPUS_TOOLS, COMPLIANCE_TOOLS, GRIEVANCE_TOOLS, SUPERVISOR_TOOLS
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    intent: str
    sender: str


llm = get_llm()

# --- Logical Agents ---
supervisor_agent = llm.bind_tools(SUPERVISOR_TOOLS)
academic_agent = llm.bind_tools(ACADEMIC_TOOLS)
finance_agent = llm.bind_tools(FINANCE_TOOLS)
hr_agent = llm.bind_tools(HR_TOOLS)
campus_agent = llm.bind_tools(CAMPUS_TOOLS)
compliance_agent = llm.bind_tools(COMPLIANCE_TOOLS)
grievance_agent = llm.bind_tools(GRIEVANCE_TOOLS)

MULTILINGUAL_RULES = """
CRITICAL RULES FOR RESPONSE GENERATION:
1. LANGUAGE MATCHING: Respond in the EXACT SAME language the Principal used (English, Hindi, Hinglish, Gujarati).
2. DATA INTEGRITY: DO NOT translate authoritative database values (names, IDs, statuses).
3. NO HALLUCINATION: If a tool returns an error, inform the Principal honestly. NEVER guess data.
4. PROACTIVE BRIEFING: If asked for a daily briefing or college summary, use the get_principal_daily_briefing tool and format the output as a professional markdown report.
"""


def supervisor_node(state):
    system_prompt = SystemMessage(content=f"""You are the Principal AI Supervisor. 
    Analyze the user's request.
    - If it's a generic greeting, daily briefing, or "college summary" request, use the get_principal_daily_briefing tool.
    - Otherwise, classify intent into: SPECIFIC_ACADEMIC, SPECIFIC_FINANCE, SPECIFIC_HR, SPECIFIC_CAMPUS, SPECIFIC_COMPLIANCE, SPECIFIC_GRIEVANCE, BROAD_REPORT, or EXPLICIT_REPORT.
    Reply with the intent keyword or call the briefing tool.
    {MULTILINGUAL_RULES}""")

    response = supervisor_agent.invoke([system_prompt] + state["messages"])
    intent = response.content.strip().upper() if not response.tool_calls else "BRIEFING"
    return {"messages": [response], "intent": intent, "sender": "Supervisor"}


def route_from_supervisor(state):
    intent = state.get("intent", "SPECIFIC_ACADEMIC")

    # If supervisor called a tool (like briefing), route to tools
    if intent == "BRIEFING":
        return "Supervisor Tools"

    if intent == "BROAD_REPORT":
        return ["Academic Agent", "Finance Agent", "HR Agent", "Campus Agent"]
    elif intent == "EXPLICIT_REPORT":
        return ["Academic Agent", "Finance Agent", "HR Agent", "Campus Agent", "Compliance Agent", "Grievance Agent"]

    mapping = {
        "SPECIFIC_ACADEMIC": "Academic Agent",
        "SPECIFIC_FINANCE": "Finance Agent",
        "SPECIFIC_HR": "HR Agent",
        "SPECIFIC_CAMPUS": "Campus Agent",
        "SPECIFIC_COMPLIANCE": "Compliance Agent",
        "SPECIFIC_GRIEVANCE": "Grievance Agent"
    }
    return mapping.get(intent, "Academic Agent")


def academic_node(state):
    sys = SystemMessage(content=f"You are the Academic Agent. {MULTILINGUAL_RULES}")
    res = academic_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Academic Agent"}


def finance_node(state):
    sys = SystemMessage(content=f"You are the Finance Agent. {MULTILINGUAL_RULES}")

    res = finance_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Finance Agent"}


def hr_node(state):
    sys = SystemMessage(content=f"You are the HR Agent. {MULTILINGUAL_RULES}")
    res = hr_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "HR Agent"}


def campus_node(state):
    sys = SystemMessage(content=f"You are the Campus Operations Agent. {MULTILINGUAL_RULES}")
    res = campus_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Campus Agent"}


def compliance_node(state):
    sys = SystemMessage(content=f"You are the Compliance Agent. {MULTILINGUAL_RULES}")
    res = compliance_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Compliance Agent"}


def grievance_node(state):
    sys = SystemMessage(content=f"You are the Grievance Agent. {MULTILINGUAL_RULES}")
    res = grievance_agent.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Grievance Agent"}


def reporting_node(state):
    sys = SystemMessage(content=f"""You are the Reporting Agent. 
    Synthesize data into a professional Markdown Executive Summary. {MULTILINGUAL_RULES}""")
    res = llm.invoke([sys] + state["messages"])
    return {"messages": [res], "sender": "Reporting Agent"}


workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Academic Agent", academic_node)
workflow.add_node("Finance Agent", finance_node)
workflow.add_node("HR Agent", hr_node)
workflow.add_node("Campus Agent", campus_node)
workflow.add_node("Compliance Agent", compliance_node)
workflow.add_node("Grievance Agent", grievance_node)
workflow.add_node("Reporting Agent", reporting_node)

workflow.add_node("Supervisor Tools", ToolNode(SUPERVISOR_TOOLS))
workflow.add_node("Academic Tools", ToolNode(ACADEMIC_TOOLS))
workflow.add_node("Finance Tools", ToolNode(FINANCE_TOOLS))
workflow.add_node("HR Tools", ToolNode(HR_TOOLS))
workflow.add_node("Campus Tools", ToolNode(CAMPUS_TOOLS))
workflow.add_node("Compliance Tools", ToolNode(COMPLIANCE_TOOLS))
workflow.add_node("Grievance Tools", ToolNode(GRIEVANCE_TOOLS))

workflow.set_entry_point("Supervisor")

workflow.add_conditional_edges("Supervisor", route_from_supervisor, {
    "Supervisor Tools": "Supervisor Tools",
    "Academic Agent": "Academic Agent",
    "Finance Agent": "Finance Agent",
    "HR Agent": "HR Agent",
    "Campus Agent": "Campus Agent",
    "Compliance Agent": "Compliance Agent",
    "Grievance Agent": "Grievance Agent"
})

# Supervisor Tools -> back to Supervisor (to generate the markdown briefing)
workflow.add_edge("Supervisor Tools", "Supervisor")


def route_after_agent(state):
    intent = state.get("intent", "SPECIFIC")
    if state["messages"][-1].tool_calls:
        return "tools"
    if intent in ["BROAD_REPORT", "EXPLICIT_REPORT"]:
        return "Reporting Agent"
    return END


agent_tool_map = {
    "Academic Agent": "Academic Tools",
    "Finance Agent": "Finance Tools",
    "HR Agent": "HR Tools",
    "Campus Agent": "Campus Tools",
    "Compliance Agent": "Compliance Tools",
    "Grievance Agent": "Grievance Tools"
}

for agent, tool_node in agent_tool_map.items():
    workflow.add_conditional_edges(agent, lambda state, an=agent: route_after_agent(state), {
        "tools": tool_node,
        "Reporting Agent": "Reporting Agent",
        END: END
    })
    workflow.add_edge(tool_node, agent)

workflow.add_edge("Reporting Agent", END)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
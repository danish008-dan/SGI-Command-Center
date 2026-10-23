# ai/teacher_graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

from ai.teacher_gateway import get_teacher_llm
from ai.teacher_tools import ALL_TEACHER_TOOLS


class TeacherAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    sender: str


llm = get_teacher_llm()
supervisor_agent = llm.bind_tools(ALL_TEACHER_TOOLS)

MULTILINGUAL_RULES = """
CRITICAL RULES FOR RESPONSE GENERATION:
1. LANGUAGE MATCHING: Respond in the EXACT SAME language the Teacher used (English, Hindi, Hinglish, Gujarati).
2. DATA INTEGRITY: DO NOT translate authoritative database values (names, IDs, statuses).
3. NO HALLUCINATION: If a tool returns an error, inform the Teacher honestly. NEVER guess data.
4. ACTION SAFETY: For execute actions, clearly state what will happen and ask for confirmation. If an action fails, report it accurately.
5. AUTHORITY BOUNDARY: You are an AI Assistant. You CANNOT submit marks, approve results, or modify attendance. You can only prepare academic content like Lesson Plans for the Teacher to review.
"""


def supervisor_node(state):
    system_prompt = SystemMessage(content=f"""You are the Teacher AI Supervisor. 
    Analyze the Teacher's request and call the appropriate tool.
    - For querying academic risks, attendance analytics, or workload: Call the respective Read tool.
    - For creating and saving a Lesson Plan: Call the save_lesson_plan_draft_tool.
    {MULTILINGUAL_RULES}""")

    response = supervisor_agent.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "sender": "Supervisor"}


# --- Build Graph ---
workflow = StateGraph(TeacherAgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Tools", ToolNode(ALL_TEACHER_TOOLS))


def route_from_supervisor(state):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "Tools"
    return END


workflow.set_entry_point("Supervisor")
workflow.add_conditional_edges("Supervisor", route_from_supervisor, {
    "Tools": "Tools",
    END: END
})

# Route back from tools to supervisor to generate final response
workflow.add_edge("Tools", "Supervisor")

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
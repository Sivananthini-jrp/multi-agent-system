from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from state import AgentState
from agents.supervisor import supervisor_node
from agents.researcher import researcher_node
from agents.analyst import analyst_node
from agents.writer import writer_node


def route_condition(state: AgentState) -> str:
    nxt = state.get("next_agent", "researcher")
    print(f"[router] → {nxt}")
    return END if nxt == "finish" else nxt


def build_graph():
    wf = StateGraph(AgentState)
    wf.add_node("supervisor", supervisor_node)
    wf.add_node("researcher", researcher_node)
    wf.add_node("analyst", analyst_node)
    wf.add_node("writer", writer_node)

    wf.add_edge(START, "supervisor")
    wf.add_conditional_edges("supervisor", route_condition, {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        END: END,
    })
    for node in ["researcher", "analyst", "writer"]:
        wf.add_edge(node, "supervisor")

    return wf.compile()


app = build_graph()
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_model
from state import AgentState

WRITER_PROMPT = """You are a Senior Writer. Synthesize research findings and analysis into a polished response. Structure: intro, body, conclusion. Address the original task directly. Be professional and actionable."""


def writer_node(state: AgentState) -> dict:
    try:
        print("[writer] starting")
        model = get_model(temperature=0.3)

        research = state.get("research_findings") or "No research available"
        analysis = state.get("analysis") or "No analysis available"
        errors = state.get("error") or ""

        context = f"""Original Task: {state['task']}

Research Findings:
{research}

Analysis:
{analysis}"""
        if errors:
            context += f"\n\nError Notes: {errors}"

        response = model.invoke([
            SystemMessage(content=WRITER_PROMPT),
            HumanMessage(content=context),
        ])
        print(f"[writer] produced {len(response.content)} chars")

        return {
            "draft": response.content,
            "final_answer": response.content,
            "messages": [response],
            "next_agent": "finish",
        }

    except Exception as e:
        print(f"[writer] FAILED: {e}")
        return {
            "error": f"Writer failed: {e}",
            "draft": f"[writer failed: {e}]",
            "final_answer": f"Could not generate final answer: {e}",
            "next_agent": "finish",
        }
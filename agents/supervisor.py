from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_model
from state import AgentState

SUPERVISOR_PROMPT = """You coordinate three agents: researcher, analyst, writer.

Reply with EXACTLY ONE WORD — nothing else:
- "researcher" if research_findings is missing
- "analyst" if analysis is missing
- "writer" if draft is missing
- "finish" if all three are done"""

def _deterministic_route(state: AgentState) -> str:
    if not state.get("research_findings"): return "researcher"
    if not state.get("analysis"): return "analyst"
    if not state.get("draft"): return "writer"
    return "finish"

def supervisor_node(state: AgentState) -> dict:
    # 1. Hard guard: all outputs present → finish
    if state.get("research_findings") and state.get("analysis") and state.get("draft"):
        print("[supervisor] all outputs present → finish")
        return {"next_agent": "finish"}

    # 2. Hard guard: loop protection
    if len(state.get("messages", [])) >= 6:
        print("[supervisor] loop guard → finish")
        return {"next_agent": "finish"}

    try:
        model = get_model(temperature=0)
        context = f"""research_findings present: {bool(state.get('research_findings'))}
analysis present: {bool(state.get('analysis'))}
draft present: {bool(state.get('draft'))}

Next agent (one word):"""
        
        response = model.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=context),
        ])
        
        raw = (response.content or "").strip().lower()
        # Take the first word in case the model adds punctuation or extra text
        word = "".join(c for c in raw.split()[0] if c.isalpha()) if raw else ""

        valid = {"researcher", "analyst", "writer", "finish"}
        chosen = word if word in valid else _deterministic_route(state)
        print(f"[supervisor] chose: {chosen} (raw: {raw[:30]!r})")

        # Override inconsistent choice
        if chosen == "researcher" and state.get("research_findings"):
            chosen = _deterministic_route(state)
        elif chosen == "analyst" and state.get("analysis"):
            chosen = _deterministic_route(state)
        elif chosen == "writer" and state.get("draft"):
            chosen = _deterministic_route(state)

        return {"next_agent": chosen}

    except Exception as e:
        fallback = _deterministic_route(state)
        print(f"[supervisor] failed ({e}) → fallback: {fallback}")
        return {"next_agent": fallback, "error": f"Supervisor fallback: {e}"}
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_model
from state import AgentState
from tools import calculate

ANALYST_PROMPT = """You are a Data Analyst. Review findings critically. Identify patterns, gaps, or errors. Use calculate tool for math. Output: key insights (2-3), quality assessment, recommendations."""

def analyst_node(state: AgentState) -> dict:
    try:
        print("[analyst] starting")
        model = get_model()
        model_with_tools = model.bind_tools([calculate])

        findings = state.get("research_findings") or "No findings available"
        messages = [
            SystemMessage(content=ANALYST_PROMPT),
            HumanMessage(content=f"Task: {state['task']}\n\nFindings:\n{findings}"),
        ]

        response = model_with_tools.invoke(messages)
        
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc.get("name") if isinstance(tc, dict) else tc.name
                tool_args = tc.get("args") if isinstance(tc, dict) else tc.args
                
                if tool_name == "calculate":
                    result = calculate.invoke(tool_args)
                else:
                    result = "Unknown tool"
                    
                messages.append(response)
                messages.append(HumanMessage(content=f"Result: {result}"))
            response = model_with_tools.invoke(messages)

        print(f"[analyst] produced {len(response.content)} chars")
        return {
            "analysis": response.content,
            "messages": [response],
            "next_agent": "writer",
        }

    except Exception as e:
        print(f"[analyst] FAILED: {e}")
        return {
            "error": f"Analyst failed: {e}",
            "analysis": f"[analysis failed: {e}]",
            "next_agent": "writer",
        }
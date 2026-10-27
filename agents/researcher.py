from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_model
from state import AgentState
from tools import calculate, word_count

RESEARCHER_PROMPT = """You are a Research Specialist. Analyze the task, use tools when helpful, and produce 3-5 bullet-point findings. Be concise."""

def researcher_node(state: AgentState) -> dict:
    try:
        print("[researcher] starting")
        model = get_model()
        model_with_tools = model.bind_tools([calculate, word_count])

        messages = [
            SystemMessage(content=RESEARCHER_PROMPT),
            HumanMessage(content=f"Task: {state['task']}"),
        ]

        response = model_with_tools.invoke(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                # Safely extract tool name and args
                tool_name = tc.get("name") if isinstance(tc, dict) else tc.name
                tool_args = tc.get("args") if isinstance(tc, dict) else tc.args
                
                if tool_name == "calculate":
                    result = calculate.invoke(tool_args)
                elif tool_name == "word_count":
                    result = word_count.invoke(tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"
                    
                messages.append(response)
                messages.append(HumanMessage(content=f"Tool {tool_name} result: {result}"))
            response = model_with_tools.invoke(messages)

        print(f"[researcher] produced {len(response.content)} chars")
        return {
            "research_findings": response.content,
            "messages": [response],
            "next_agent": "analyst",
        }

    except Exception as e:
        print(f"[researcher] FAILED: {e}")
        return {
            "error": f"Researcher failed: {e}",
            "research_findings": f"[research failed: {e}]",
            "next_agent": "analyst",
        }
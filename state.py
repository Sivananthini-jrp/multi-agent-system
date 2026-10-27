from __future__ import annotations
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task: str
    research_findings: Optional[str]
    analysis: Optional[str]
    draft: Optional[str]
    final_answer: Optional[str]
    next_agent: Optional[str]
    error: Optional[str]
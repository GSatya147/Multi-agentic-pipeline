from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    researcher_notes: list[dict]
    researcher_count: int
    writer_notes: dict
    supervisor_notes: str
    supervisor_count: int
    step_count: int 
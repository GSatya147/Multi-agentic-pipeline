from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    researcher_notes: list[dict]
    writer_notes: dict
    supervisor_notes: dict
    supervisor_counter: int
    step_counter: int 
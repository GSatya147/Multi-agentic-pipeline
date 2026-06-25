from langfuse import observe

from src.state import AgentState
from src.clients import supervisor_model, researcher_model, writer_model
from src.config import SUPERVISOR_MAX_COUNT, RESEARCHER_MAX_COUNT
from src.tools import get_tools_schema, run_search_tool

@observe(name="supervisor_node")
def supervisor_node(state: AgentState)-> list[dict]:
    if state.get("writer_notes") and state.get("supervisor_count") <= SUPERVISOR_MAX_COUNT:
        response = supervisor_model(state["writer_notes"])
    else:
        response = "please check writer node"

    return [{"messages" : [response], "supervisor_notes" : response, "supervisor_count" : state["supervisor_count"] + 1, "step_count" : state["step_count"] + 1}]    

@observe(name="researcher_node")
def researcher_node(state: AgentState):
    i = 0
    results: list[dict] = []
    while i < RESEARCHER_MAX_COUNT:
        response = researcher_model(state["messages"], tools_schema=get_tools_schema())
        tool_name = state["messages"][-1].tool_calls[0]["name"]

        if response.tool_calls:
            if tool_name == "search_tool":
                search_query = state["messages"][-1].tool_calls[0]["args"]["query"]
                results+=run_search_tool(query=search_query)

                tool_message = {
                    "tool_name" : tool_name,
                    "content" : results,
                    "tool_call_id" : state["messages"][-1].tool_calls[0]["id"]
                }

                i+=1
                return [{"messages" : [tool_message], "researcher_notes" : response, "step_count" : state["step_count"] + 1, "researcher_count" : state["researcher_count"] + 1}]
            
            else:
                tool_message = {
                    
                }
        else:
            break
    
    return 
    
    
@observe(name="writer_node")
def writer_node(state: AgentState):
    response = writer_model(state["messages"])

    return [{"messages" : [response], "writer_notes" : response, "step_count" : state["step_count"] + 1}]

@observe(name="final_node")
def final_node(state: AgentState):
    return state["writer_notes"]

@observe(name="routing_logic")
def routing_logic(state: AgentState):
    if state.get("supervisor_notes") == "approved":
        return "final_node"
    else:
        return "writer_node"

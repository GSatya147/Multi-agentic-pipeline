import json

from dotenv import load_dotenv
from langfuse import observe

from src.state import AgentState
from src.clients import supervisor_model, researcher_model, writer_model
from src.config import SUPERVISOR_MAX_COUNT, RESEARCHER_MAX_COUNT
from src.tools import get_tools_schema, run_search_tool

load_dotenv()

@observe(name="supervisor_node")
def supervisor_node(state: AgentState)-> list[dict]:
    if state.get("writer_notes"):
        response = supervisor_model(state["messages"])
    else:
        response = "please check the writer node"

    return {"messages" : [response], "supervisor_notes" : response.get("content"), "supervisor_count" : state["supervisor_count"] + 1, "step_count" : state["step_count"] + 1}

@observe(name="researcher_node")
def researcher_node(state: AgentState):
    response = researcher_model(state["messages"], tools_schema=get_tools_schema())
    
    return {"messages" : [response], "step_count" : state["step_count"] + 1}

@observe(name="search_tool")
def search_tool(state: AgentState):
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]

    if tool_name == "search_tool":
        if state["researcher_count"] <= RESEARCHER_MAX_COUNT:
            search_query = state["messages"][-1].tool_calls[0]["args"]["query"]
            results = run_search_tool(query=search_query)

            tool_message = {
                "role" : "tool",
                "content" : results,
                "tool_call_id" : tool_call_id
            }

            return {"messages" : [tool_message], "researcher_notes" : results, "step_count" : state["step_count"] + 1, "researcher_count" : state["researcher_count"] + 1}
        
        else:
            tool_message = {
                "role" : "tool",
                "content" : "Researcher has exhausted tool limits",
                "tool_call_id" : tool_call_id
            }
            return {"messages" : [tool_message], "step_count" : state["step_count"] + 1}

@observe(name="writer_node")
def writer_node(state: AgentState):
    response = writer_model(state["messages"])

    return {"messages" : [response], "writer_notes" : response, "step_count" : state["step_count"] + 1}

@observe(name="final_node")
def final_node(state: AgentState):
    result = state["writer_notes"]
    return {"messages" : [result], "step_count" : state["step_count"] + 1}

@observe(name="researcher_routing")
def researcher_routing(state: AgentState):
    if state["messages"][-1].tool_calls:
        return "search_tool"
    else:
        return "writer_node"
    
@observe(name="routing_logic")
def routing_logic(state: AgentState):
    if state["supervisor_count"] > SUPERVISOR_MAX_COUNT:
        return "final_node"
    
    if state["supervisor_notes"].lower() == "approved":
        return "final_node"
    else:
        return "writer_node"

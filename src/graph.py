import logging
import sys

from langgraph.graph import StateGraph, START, END 
from langgraph.checkpoint.memory import InMemorySaver

from src.state import AgentState
from src.nodes import (
    final_node,
    researcher_node,
    researcher_routing,
    routing_logic,
    search_tool,
    supervisor_node,
    writer_node
)


logging.basicConfig(
    level = logging.INFO,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class AgentGraph:
    def __init__(self):
        self.graph = StateGraph(AgentState)
        checkpointer = InMemorySaver()

        # add nodes
        self.graph.add_node("supervisor_node", supervisor_node)
        self.graph.add_node("researcher_node", researcher_node)
        self.graph.add_node("search_tool", search_tool)
        self.graph.add_node("writer_node", writer_node)
        self.graph.add_node("final_node", final_node)

        # add edges
        self.graph.add_edge(START, "researcher_node")
        self.graph.add_edge("writer_node", "supervisor_node")
        self.graph.add_edge("search_tool", "researcher_node")
        self.graph.add_edge("final_node", END)

        # add conditional edges
        self.graph.add_conditional_edges("researcher_node", researcher_routing)
        self.graph.add_conditional_edges("supervisor_node", routing_logic)

        # compile
        self.app = self.graph.compile(checkpointer=checkpointer, interrupt_before=["writer_node","final_node"])


    def invoke_graph(self, query: str, initial_state: dict, thread_id: int):
        config: dict = {
            "configurable" : {
                "thread_id" : f"thread_{thread_id}"
            }
        }

        try:
            snapshot = self.app.get_state(config=config)

            if snapshot.values:
                self.app.invoke({"messages" : [{"role" : "user", "content" : query}]}, config=config)
                return self.app.get_state(config=config)
            else:
                self.app.invoke(initial_state, config=config)
                return self.app.get_state(config=config)

        except Exception as e:
            logger.error(e)

    def get_history(self, thread_id):
        config = {
            "configurable" : {
                "thread_id" : f"thread_{thread_id}"
            }
        }

        snapshot = self.app.get_state(config=config)
        if snapshot.values:
            return snapshot.values["messages"]
        else:
            return "No history"
    
    def resume_graph(self, thread_id):
        config = {
            "configurable" : {
                "thread_id" : f"thread_{thread_id}"
            }
        }

        self.app.invoke(None, config=config)
        return self.app.get_state(config=config)

    def modify_and_resume(self, modified, thread_id):
        config = {
            "configurable" : {
                "thread_id" : f"thread_{thread_id}"
            }
        }

        self.app.update_state({"messages" : [{"role" : "assistant", "content" : modified}]}, config=config)
        self.app.invoke(None, config=config)

    def get_final_response(self, thread_id):
        config = {
            "configurable" : {
                "thread_id" : f"thread_{thread_id}"
            }
        }

        snapshot = self.app.get_state(config=config)
        if snapshot.values:
            return snapshot.values["writer_notes"]
        else:
            return "No response"
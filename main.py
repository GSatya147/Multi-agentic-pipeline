import os
import logging
import sys

from src.graph import AgentGraph

logging.basicConfig(
    level = logging.INFO,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

graph = AgentGraph()
while True:
    try:
        thread_id = int(input(">> Enter Thread ID: "))
        query = input(">> ")
        initial_state = {
            "messages" : [{
                "role" : "user",
                "content" : query,
            }],
            "supervisor_count": 0,
            "researcher_count": 0,
            "researcher_notes": [],
            "writer_notes": {},
            "supervisor_notes": {},
            "step_count" : 0
        }

        if query.lower() == "history":
            history = graph.get_history(thread_id=thread_id)
            logger.info("History: ", history)
        
        else:
            snapshot = graph.invoke_graph(query, initial_state, thread_id)

            if "writer_node" in snapshot.next:
                logger.info(f"HITL : before -> writer node\n")

                user_pref = input(">> Approve? (y/n): ")
                if user_pref.lower() == "y":
                    snapshot = graph.resume_graph(thread_id=thread_id)
                else:
                    modified = input(">> modified content: ")
                    graph.modify_and_resume(modified, thread_id=thread_id)
            
            if snapshot and "final_node" in snapshot.next:
                logger.info(f"HITL : before -> final node\n")

                user_pref = input(">> Approve final report? (y/n): ")
                if user_pref.lower() == "y":
                    graph.resume_graph(thread_id=thread_id)
                    response = graph.get_final_response(thread_id=thread_id)
                    logger.info(response)
                else:
                    modified = input(">> modified content: ")
                    graph.modify_and_resume(modified, thread_id=thread_id)
                    response = graph.get_final_response(thread_id=thread_id)
                    logger.info(response)
    
    except KeyboardInterrupt as e:
        print(e)
        break

    except Exception as e:
        print(e)
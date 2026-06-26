import os
import json
import logging
import sys

from dotenv import load_dotenv
from litellm import (
    completion, 
    RateLimitError, 
    APIError, 
    ServiceUnavailableError, 
    Timeout, 
    AuthenticationError, 
    BadRequestError
)

from langchain_core.messages import (
    AIMessage,
    HumanMessage, 
    ToolMessage
)

from src.config import SUPERVISOR_MODEL, RESEARCHER_MODEL, WRITER_MODEL, WRITER_MAX_TOKENS


logging.basicConfig(
    level = logging.INFO,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

load_dotenv()

def convert_messages(messages_dict)-> list[dict]:
    converted_dict:list[dict] = []
    for message in messages_dict:
        if isinstance(message, HumanMessage):
            converted_dict.append({
                "role" : "user",
                "content" : message.content
            })

        elif isinstance(message, AIMessage):
            if message.tool_calls:
                converted_dict.append({
                    "role" : "assistant",
                    "content" : message.content,
                    "tool_calls" : [{
                        "id" : tool.get("id"),
                        "type" : "function",
                        "function" : {
                            "name" : tool.get("name"),
                            "arguments" : json.dumps(tool.get("args"))
                        }
                    } for tool in message.tool_calls]
                })
            
            else:
                converted_dict.append({
                    "role" : "assistant",
                    "content" : message.content
                })

        elif isinstance(message, ToolMessage):
            converted_dict.append({
                "role" : "tool",
                "content" : message.content,
                "tool_call_id" : message.tool_call_id
            })

    return converted_dict

def supervisor_model(messages):
    converted_messages = convert_messages(messages_dict=messages)

    sys_prompt = """
    <context>
    You are a supervisor evaluating a written report produced by a writer agent.
    The last AI message in the conversation is the report to evaluate.
    1. Return ONLY the string "approved" if acceptable.
    2. Return ONLY valid JSON {"status": "unapproved", "suggestions": "..."} if not.
    3. Nothing else. No explanation. No conversation.
    4. Be generous.
    </context>
    <examples>
    1. "approved"
    2. {"status" : "unapproved", "suggestions" : "..."}
    </examples>
    """

    context = [{"role" : "system", "content" : sys_prompt}] + converted_messages
    try:
        response = completion(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model=SUPERVISOR_MODEL,
            messages=context,
        )

        message = response.choices[0].message.model_dump()
        return message
    
    except RateLimitError as e:
            print(f"Rate limit error: {e.message}")

    except APIError as e:
            print(f"API error: {e.message} ")

    except BadRequestError as e:
            print(f"Bad request error: {e.message} ")

    except Timeout as e:
            print(f"Time out error: {e.message} ")
        
    except AuthenticationError as e:
            print(f"Auth error: {e.message} ")

    except ServiceUnavailableError as e:
            print(f"Service unavailable error: {e.message} ")

    except Exception as e:
            print(f"Unexpected error: {e}")

def researcher_model(messages, tools_schema):
    converted_messages = convert_messages(messages_dict=messages)

    sys_prompt = """
    <context>
    You are a researcher, use specific search queries to initiate web search regarding the topic given. return factually claimed results from the tools available.
    </context>
    """
    context = [{"role" : "system", "content" : sys_prompt}] + converted_messages

    try:
        response = completion(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model=RESEARCHER_MODEL,
            messages=context,
            tools=tools_schema
        )

        message = response.choices[0].message.model_dump()
        return message
    
    except RateLimitError as e:
            print(f"Rate limit error: {e.message}")

    except APIError as e:
            print(f"API error: {e.message} ")

    except BadRequestError as e:
            print(f"Bad request error: {e.message} ")

    except Timeout as e:
            print(f"Time out error: {e.message} ")
        
    except AuthenticationError as e:
            print(f"Auth error: {e.message} ")

    except ServiceUnavailableError as e:
            print(f"Service unavailable error: {e.message} ")

    except Exception as e:
            print(f"Unexpected error: {e}")

def writer_model(messages):
    converted_messages = convert_messages(messages_dict=messages)

    sys_prompt = """
    <context>
    You are a writer, who synthesises a short report well under 750 words. With relevant short headings, bulleted points wherever applicable and in-text citation of source you used, ONLY answer from the provided context.
    </context>
    """
    context = [{"role" : "system", "content" : sys_prompt}] + converted_messages

    try:
        response = completion(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model=WRITER_MODEL,
            messages=context,
            max_tokens=WRITER_MAX_TOKENS
        )

        message = response.choices[0].message.model_dump()
        return message
    
    except RateLimitError as e:
            print(f"Rate limit error: {e.message}")

    except APIError as e:
            print(f"API error: {e.message} ")

    except BadRequestError as e:
            print(f"Bad request error: {e.message} ")

    except Timeout as e:
            print(f"Time out error: {e.message} ")
        
    except AuthenticationError as e:
            print(f"Auth error: {e.message} ")

    except ServiceUnavailableError as e:
            print(f"Service unavailable error: {e.message} ")

    except Exception as e:
            print(f"Unexpected error: {e}")
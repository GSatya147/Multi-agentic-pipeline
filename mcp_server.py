import os
import logging
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
from tavily.errors import (
    BadRequestError, 
    InvalidAPIKeyError, 
    ForbiddenError, 
    MissingAPIKeyError,
    UsageLimitExceededError 
)

load_dotenv()

logging.basicConfig(
    level = logging.INFO,
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

mcp = FastMCP("web_search")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def format_response(response) -> list[dict]:
    result_list: list[dict] = []

    for result in response.get("results")[:3]:
        result_list.append({
            "title" : result.get("title"),
            "content" : result.get("content"),
            "source" : result.get("url")
        })
    
    return result_list

@mcp.tool()
def search_tool(query, client=tavily_client)-> list[dict]:
    try:
        response = client.search(query)

        result: list[dict] = format_response(response)
        return result
    
    except InvalidAPIKeyError:
        logger.error("Invalid API key error")
        return({"error" : "Invalid API key error", "query" : query})

    except MissingAPIKeyError:
        logger.error("Missing API key error")
        return({"error" : "Missing API key error", "query" : query})

    except BadRequestError:
        logger.error("Bad request (missing/wrong parameters) error")
        return({"error" : "Bad request (missing/wrong parameters) error", "query" : query})

    except ForbiddenError:
        logger.error("Forbidden (url not supported) error")
        return({"error" : "Forbidden (url not supported) error", "query" : query})

    except UsageLimitExceededError:
        logger.error("Usage limit exceeded error")
        return({"error" : "Usage limit exceeded error", "query" : query})

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return({"error" : str(e), "query" : query})

def main()-> None:
    mcp.run(transport="stdio")

if __name__=="__main__":
    main()

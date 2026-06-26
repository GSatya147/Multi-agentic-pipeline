import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

SEARCH_TOOL_SCHEMA = {
            "type" : "function",
            "function" : {
                "name" : "search_tool",
                "description" : "use web search when the context is inadequate, or when user requests for it. Be factual about claims use the web search for confirmation whenever applicable",
                "parameters" : {
                    "type" : "object",
                    "properties" : {
                        "query" : {
                            "type" : "string",
                            "description" : "a simple string type query to perform the web search efficiently",
                        }
                    },
                    "required" : ["query"],
                }
            }
        }

client_config: dict = {
    "web_search" : {                # Name of FastMCP
        "command" : "python",       # What to run
        "args" : ["mcp_server.py"], # Which file
        "transport" : "stdio"       # How they talk
    }
}

async def _run_search_tool(query):
    client = MultiServerMCPClient(client_config)
    tools = await client.get_tools()

    tool = next((t for t in tools if t.name=="search_tool"), None) # A generator, evals and return the first success iter
    if tool is None:
        raise ValueError("search_tool not found on MCP server")
    
    return await tool.ainvoke({"query" : query})

def run_search_tool(query):
    result = asyncio.run(_run_search_tool(query=query))
    return result

def get_tools_schema():
    tools_schema: list[dict] = [SEARCH_TOOL_SCHEMA]
    return tools_schema

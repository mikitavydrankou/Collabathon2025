"""
MCP Server for Banking Chat App Money Transfer Tools.

This server exposes three tools via the Model Context Protocol:
1. first_suggestion_tool - Initial payment suggestions
2. filter_suggestion_tool - Filtered payment suggestions
3. final_check_tool - Transaction validation and consistency checking
"""

import json
import logging
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import ValidationError

from shared.models import engine

from . import __version__
from .tools import TOOLS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

# Initialize MCP server
app = Server("banking-money-transfer-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools.

    This is called by MCP clients to discover available tools.
    """
    tools = []

    for tool_name, tool_info in TOOLS.items():
        # Convert Pydantic schema to JSON schema for input
        input_schema = tool_info["input_schema"].model_json_schema()

        tools.append(
            Tool(
                name=tool_name,
                description=tool_info["description"],
                inputSchema=input_schema,
            )
        )

    logger.info(f"Listed {len(tools)} available tools")
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """
    Execute a tool with the provided arguments.

    Args:
        name: Tool name
        arguments: Tool input arguments

    Returns:
        List containing a single TextContent with the JSON result
    """
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name not in TOOLS:
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    tool_info = TOOLS[name]

    try:
        # Validate and parse input
        input_schema = tool_info["input_schema"]
        validated_input = input_schema(**arguments)

        # Execute tool
        result = tool_info["function"](validated_input)

        # Convert result to JSON
        if hasattr(result, "model_dump"):
            output_dict = result.model_dump()
        else:
            output_dict = result

        output_json = json.dumps(output_dict, default=str)
        logger.info(f"Tool {name} executed successfully")

        return [TextContent(type="text", text=output_json)]

    except ValidationError as e:
        error_msg = f"Input validation error: {str(e)}"
        logger.error(f"Tool {name} validation error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    except Exception as e:
        error_msg = f"Tool execution error: {str(e)}"
        logger.error(f"Tool {name} execution error: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]


def check_health() -> Dict[str, Any]:
    """
    Check server health including database connectivity.

    Returns:
        Dict with health status information
    """
    try:
        # Test database connection
        connection = engine.connect()
        connection.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": __version__,
        "database": db_status,
        "tools": list(TOOLS.keys()),
    }


async def main():
    """
    Main entry point for the MCP server.

    Starts the server and listens for MCP protocol messages over stdio.
    """
    logger.info(f"Starting Banking Money Transfer MCP Server v{__version__}")

    # Log health check
    health = check_health()
    logger.info(f"Health check: {health}")

    if health["status"] != "healthy":
        logger.warning(
            "Server starting with unhealthy status - database connection issues detected"
        )

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

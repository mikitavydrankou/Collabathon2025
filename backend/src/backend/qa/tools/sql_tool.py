"""
SQL query tool for executing database queries via MCP server.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SQLTool:
    """Tool for executing SQL queries against transaction database via MCP server."""
    
    def __init__(self):
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
        self.available_functions = [
            "get_recent_transactions",
            "filter_transactions",
            "get_time_based_transactions",
            "get_recipient_patterns",
            "get_user_balance"
        ]
    
    def get_schema_info(self) -> str:
        """Returns database schema information for LLM."""
        return """
Available database functions:

1. get_recent_transactions(user_id: int, limit: int = 10)
   - Returns recent transactions for user
   
2. filter_transactions(user_id: int, recipient_name?: str, amount?: float, title?: str)
   - Filter transactions by various criteria
   
3. get_time_based_transactions(user_id: int)
   - Get transactions from 1 year, 1 month, 1 week ago
   
4. get_recipient_patterns(user_id: int)
   - Analyze common recipients and their accounts
   
5. get_user_balance(user_id: int)
   - Get current user balance
"""
    
    def execute(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a database function with given parameters via MCP server.
        
        Args:
            function_name: Name of the function to execute
            params: Parameters for the function
            
        Returns:
            Dict with success status and data/error
        """
        logger.info(f"\n[EXEC] SQL TOOL - Executing Function")
        logger.info(f"{'-'*60}")
        logger.info(f"Function: {function_name}")
        logger.info(f"Parameters: {json.dumps(params, indent=2)}")
        
        if function_name not in self.available_functions:
            logger.error(f"    [NO] Unknown function: {function_name}")
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }
        
        try:
            # Call MCP server
            user_id = params.get("user_id", 1)
            
            payload = {
                "user_id": user_id,
                "function_name": function_name,
                "parameters": params
            }
            
            logger.info(f"    [NET] Calling MCP server: {self.mcp_server_url}/tools/sql-query")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.mcp_server_url}/tools/sql-query",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                success = result.get("success", False)
                data_count = len(result.get("data", [])) if isinstance(result.get("data"), list) else 1
                
                logger.info(f"    {'[OK]' if success else '[NO]'} MCP Response - Success: {success}, Count: {data_count}")
                
                return {
                    "success": success,
                    "data": result.get("data"),
                    "error": result.get("error"),
                    "count": data_count
                }
            
        except httpx.HTTPError as e:
            logger.error(f"    [NO] MCP server HTTP error: {str(e)}")
            return {"success": False, "error": f"MCP server error: {str(e)}"}
        except Exception as e:
            logger.error(f"    [NO] Error: {str(e)}")
            return {"success": False, "error": f"Error: {str(e)}"}
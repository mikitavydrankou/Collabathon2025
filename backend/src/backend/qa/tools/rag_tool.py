"""
RAG tool for similarity search on transaction descriptions.
"""
from typing import Dict, List, Any
import json
import httpx
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RAGTool:
    """Tool for finding similar transactions using semantic search."""
    
    def __init__(self, mcp_server_url: str = None):
        self.top_k = 3
        self.mcp_server_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "http://localhost:8001")
    
    def search_similar(self, query: str, user_id: int, top_k: int = 3) -> Dict[str, Any]:
        """
        Search for similar transactions based on query text via MCP server.
        
        Args:
            query: Search query (transaction description)
            user_id: User ID to filter transactions
            top_k: Number of results to return
            
        Returns:
            Dict with success status and similar transactions
        """
        logger.info(f"\n[EXEC] RAG TOOL - Searching Similar Transactions")
        logger.info(f"{'-'*60}")
        logger.info(f"Query: '{query}'")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Top K: {top_k}")
        
        try:
            # Call MCP server
            payload = {
                "user_id": user_id,
                "query": query,
                "top_k": top_k
            }
            
            logger.info(f"\n📡 Calling MCP Server")
            logger.info(f"URL: {self.mcp_server_url}/tools/rag-query")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.mcp_server_url}/tools/rag-query",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                success = result.get("success", False)
                data_count = len(result.get("data", []))
                
                logger.info(f"    {'[OK]' if success else '[NO]'} MCP Response - Success: {success}, Count: {data_count}")
                
                return {
                    "success": success,
                    "data": result.get("data", []),
                    "count": data_count,
                    "query": query,
                    "error": result.get("error")
                }
            
        except httpx.HTTPError as e:
            logger.error(f"    [NO] MCP server HTTP error: {str(e)}")
            return {"success": False, "error": f"MCP server error: {str(e)}"}
        except Exception as e:
            logger.error(f"    [NO] Error: {str(e)}")
            return {"success": False, "error": f"Error: {str(e)}"}
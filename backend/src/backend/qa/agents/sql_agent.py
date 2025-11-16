from typing import Dict, Any, Optional
import json
import logging
from ..tools.sql_tool import SQLTool
from ...chatbot.llm import call_llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SQLAgent:
    """Agent responsible for executing SQL queries through database tools."""
    
    def __init__(self):
        self.tool = SQLTool()
        self.name = "SQL Agent"
        self.system_prompt = f"""You are an agent that works with the transaction database.

Available functions in SQL Tool:
{self.tool.get_schema_info()}

Your tasks:
1. Analyze the task from the main agent
2. Select the correct SQL Tool function and parameters
3. Call the function through the tool
4. Analyze the results and decide if you can answer the question
5. Return a structured response

Respond ONLY in JSON format:
{{
  "function_to_call": "function_name",
  "parameters": {{}},
  "can_answer": true/false,
  "reasoning": "why you can or cannot answer",
  "message": "brief description of results"
}}"""
    
    def process_task(self, task: str, user_id: int, context: str = "") -> Dict[str, Any]:
        """
        Process a task that requires database querying using LLM to select function.
        
        Args:
            task: Description of what needs to be queried
            user_id: User ID for the query
            context: Previous conversation context
            
        Returns:
            Dict with result or indication that no answer found
        """
        logger.info(f"\n{'-'*80}")
        logger.info(f"[TOOL] SQL AGENT - Processing Task")
        logger.info(f"{'-'*80}")
        logger.info(f"Task: {task}")
        logger.info(f"User ID: {user_id}")
        
        # Use LLM to determine which function to call
        user_prompt = f"""User's task: {task}
User ID: {user_id}
Context: {context}

Determine which SQL Tool function needs to be called and with what parameters."""
        
        try:
            # First, ask LLM which function to use
            llm_response = call_llm(self.system_prompt, user_prompt, temperature=0.3)
            decision = json.loads(llm_response)
            
            function_name = decision.get("function_to_call")
            params = decision.get("parameters", {})
            
            logger.info(f"  Function selected: {function_name}")
            logger.info(f"  Parameters: {params}")
            
            # Add user_id to params if not present
            if "user_id" not in params:
                params["user_id"] = user_id
            
            if not function_name:
                logger.warning("  ⚠️  No function name determined")
                return {
                    "success": False,
                    "message": "Could not determine what information to retrieve from database."
                }
            
            # Execute database function through tool
            logger.info(f"  [EXEC] Calling SQL tool: {function_name}")
            tool_result = self.tool.execute(function_name, params)
            logger.info(f"  Tool result: {'[OK] Success' if tool_result['success'] else '[NO] Failed'}")
            
            if not tool_result["success"]:
                logger.error(f"  Error: {tool_result.get('error')}")
                return {
                    "success": False,
                    "message": f"Error retrieving data: {tool_result.get('error', 'Unknown error')}"
                }
            
            # Use LLM to analyze if results can answer the question
            analysis_prompt = f"""User's task: {task}

Results from SQL Tool (function {function_name}):
{json.dumps(tool_result, ensure_ascii=False, indent=2)}

Analyze whether these results can answer the user's question."""
            
            logger.info("  [LLM] Analyzing results with LLM...")
            llm_analysis = call_llm(self.system_prompt, analysis_prompt, temperature=0.3)
            analysis = json.loads(llm_analysis)
            
            # Check if we have useful data
            data = tool_result.get("data", [])
            if not data or (isinstance(data, list) and len(data) == 0):
                return {
                    "success": False,
                    "message": "No transactions found for your query.",
                    "tool_data": data
                }
            
            if not analysis.get("can_answer", False):
                return {
                    "success": False,
                    "message": analysis.get("reasoning", "Could not answer based on the found data."),
                    "tool_data": data
                }
            
            return {
                "success": True,
                "data": data,
                "function_used": function_name,
                "message": analysis.get("message", self._format_results(data, function_name)),
                "reasoning": analysis.get("reasoning", ""),
                "tool_data": data
            }
            
        except json.JSONDecodeError as e:
            # Fallback to rule-based approach
            logger.warning(f"  ⚠️  JSON decode failed: {e}, using rule-based fallback")
            function_name, params = self._parse_task(task, user_id)
            
            logger.info(f"  Fallback function: {function_name} with params: {params}")
            
            if not function_name:
                logger.error("  [NO] Could not determine function")
                return {
                    "success": False,
                    "message": "Could not determine what information to retrieve from database."
                }
            
            tool_result = self.tool.execute(function_name, params)
            
            if not tool_result["success"]:
                logger.error(f"  [NO] Tool execution failed: {tool_result.get('error')}")
                return {
                    "success": False,
                    "message": f"Error retrieving data: {tool_result.get('error', 'Unknown error')}"
                }
            
            data = tool_result.get("data", [])
            if not data or (isinstance(data, list) and len(data) == 0):
                logger.warning("  ⚠️  No data found")
                return {
                    "success": False,
                    "message": "No transactions found for your query."
                }
            
            logger.info(f"  [OK] Success with {len(data) if isinstance(data, list) else 1} results")
            return {
                "success": True,
                "data": data,
                "function_used": function_name,
                "message": self._format_results(data, function_name)
            }
        except Exception as e:
            logger.error(f"  [NO] Unexpected error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}"
            }
    
    def _parse_task(self, task: str, user_id: int) -> tuple[Optional[str], Dict[str, Any]]:
        """Parse task description to determine which database function to call."""
        task_lower = task.lower()
        
        # Balance queries
        if any(word in task_lower for word in ["balance", "how much", "money", "funds", "available"]):
            return "get_user_balance", {"user_id": user_id}
        
        # Recent transactions
        if any(word in task_lower for word in ["recent", "last", "latest", "recently", "show my"]):
            limit = 10
            # Try to extract limit if specified
            if "last" in task_lower or "recent" in task_lower:
                import re
                numbers = re.findall(r'\d+', task)
                if numbers:
                    limit = int(numbers[0])
            return "get_recent_transactions", {"user_id": user_id, "limit": limit}
        
        # Time-based queries
        if any(word in task_lower for word in ["month", "week", "year", "ago", "last month", "last week", "last year"]):
            return "get_time_based_transactions", {"user_id": user_id}
        
        # Recipient patterns
        if any(word in task_lower for word in ["patterns", "frequent", "often", "most common", "recipient"]):
            return "get_recipient_patterns", {"user_id": user_id}
        
        # Default to recent transactions
        return "get_recent_transactions", {"user_id": user_id, "limit": 10}
    
    def _format_results(self, data: Any, function_name: str) -> str:
        """Format database results into readable text."""
        if function_name == "get_user_balance":
            balance = data.get("balance", 0)
            return f"Your current balance: {balance} PLN"
        
        if isinstance(data, list):
            if len(data) == 0:
                return "No transactions found"
            
            formatted = f"Found {len(data)} transactions:\n"
            for i, transaction in enumerate(data[:5], 1):
                receiver = transaction.get("receiver_name", "Unknown")
                amount = transaction.get("amount", 0)
                text = transaction.get("transaction_text", "")
                formatted += f"{i}. {receiver} - {amount} PLN ({text})\n"
            
            return formatted
        
        return str(data)
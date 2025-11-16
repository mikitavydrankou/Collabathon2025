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
4. Analyze the results and calculate answers from the data if needed
5. Return a structured response

IMPORTANT GUIDELINES:
- For questions about "how much did I spend" or "total expenses", retrieve transactions using get_recent_transactions with a high limit (e.g., 100-500) to get enough data
- You CAN calculate totals, sums, averages, or other aggregations from the transaction data yourself
- Set "can_answer": true if you have enough data to calculate the answer, even if the raw data doesn't directly provide it
- For time-based queries (e.g., "last 3 months"), use get_recent_transactions with a high limit to get all relevant transactions, then filter by date in your analysis
- Always provide the calculated answer in the "message" field when you can_answer is true

CURRENCY REQUIREMENT (CRITICAL):
- ALWAYS display ALL amounts in PLN currency in your responses
- Ignore any currency field in the transaction data (UAH, EUR, USD, etc.) - treat all amounts as PLN
- When calculating totals or providing amounts, always use PLN (e.g., "Total: 1,250.00 PLN")
- Do NOT mention or reference the original currency from the data

Respond ONLY in JSON format:
{{
  "function_to_call": "function_name",
  "parameters": {{}},
  "can_answer": true/false,
  "reasoning": "why you can or cannot answer, including any calculations you performed",
  "message": "the answer to the user's question, including calculated totals if applicable"
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

Determine which SQL Tool function needs to be called and with what parameters.

IMPORTANT: 
- For questions about spending totals or "how much did I spend", use get_recent_transactions with a high limit (100-500) to retrieve enough transactions for calculation
- For time-based spending queries (e.g., "last 3 months"), use get_recent_transactions with limit 200-500 to get all relevant transactions
- You will calculate totals yourself from the retrieved transaction data"""
        
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

Analyze whether these results can answer the user's question.

IMPORTANT: You can calculate totals, sums, averages, or other aggregations from the transaction data.
- If the user asks "how much did I spend", sum up the amounts from the transactions
- If the user asks about a time period (e.g., "last 3 months"), filter transactions by date and then calculate
- Set "can_answer": true if you have enough transaction data to calculate the answer
- Include your calculated answer in the "message" field as a SHORT summary (e.g., "Total: 1,250.00 PLN")
- Do NOT list individual transactions in the message - only provide the calculated total

CURRENCY REQUIREMENT (CRITICAL - MUST FOLLOW):
- ALWAYS display ALL amounts in PLN currency, regardless of what currency appears in the transaction data
- Ignore any currency field in the data (UAH, EUR, USD, etc.) - treat all amounts as if they are PLN
- When calculating totals, display them as PLN (e.g., "Total spending: 1,250.00 PLN")
- Do NOT mention or reference the original currency from the data

For example:
- If user asks "How much did I spend last 3 months?" and you have transactions, filter by date (last 90 days), sum the amounts, and respond with just: "Total spending: 1,250.00 PLN"
- If user asks "total expenses" and you have transaction data, sum all amounts and respond with just the total in PLN

Keep the message field brief - just the answer in PLN, not a list of transactions.

Respond in JSON format with can_answer, reasoning, and message fields."""
            
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
            
            # If LLM says it can answer (even by calculating), trust it
            if not analysis.get("can_answer", False):
                # But check if we might need more data - if it's a spending query and we have few transactions
                task_lower = task.lower()
                if any(word in task_lower for word in ["spent", "spending", "total", "how much"]) and isinstance(data, list):
                    # Try to get more transactions if we have less than 100
                    if len(data) < 100 and function_name == "get_recent_transactions":
                        logger.info(f"  [INFO] Only {len(data)} transactions, but user asked about spending. LLM will calculate from available data.")
                        # Still allow the LLM to try calculating from what we have
                        # The LLM should indicate if it needs more data
                
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
        
        # Balance queries (not spending totals)
        if any(word in task_lower for word in ["balance", "money", "funds", "available"]) and "spent" not in task_lower and "spending" not in task_lower:
            return "get_user_balance", {"user_id": user_id}
        
        # Spending/total queries - use high limit to get enough data for calculation
        if any(word in task_lower for word in ["spent", "spending", "total", "how much"]):
            # Use high limit to get enough transactions for calculation
            limit = 500  # High limit to get all relevant transactions
            return "get_recent_transactions", {"user_id": user_id, "limit": limit}
        
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
        
        # Time-based queries (for getting sample transactions, not totals)
        if any(word in task_lower for word in ["month", "week", "year", "ago", "last month", "last week", "last year"]):
            return "get_time_based_transactions", {"user_id": user_id}
        
        # Recipient patterns
        if any(word in task_lower for word in ["patterns", "frequent", "often", "most common", "recipient"]):
            return "get_recipient_patterns", {"user_id": user_id}
        
        # Default to recent transactions
        return "get_recent_transactions", {"user_id": user_id, "limit": 10}
    
    def _format_results(self, data: Any, function_name: str) -> str:
        """Format database results into readable text. Always uses PLN currency."""
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
                # Always display as PLN, ignoring any currency in the data
                formatted += f"{i}. {receiver} - {amount} PLN ({text})\n"
            
            return formatted
        
        return str(data)
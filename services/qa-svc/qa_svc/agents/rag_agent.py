from typing import Dict, Any
import json
import logging
from ..tools.rag_tool import RAGTool
from shared.llm import call_llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RAGAgent:
    """Agent responsible for finding similar transactions using semantic search."""
    
    def __init__(self):
        self.tool = RAGTool()
        self.name = "RAG Agent"
        self.system_prompt = """You are an agent that analyzes similar transactions based on similarity search.

Your tasks:
1. Receive a task from the main agent
2. Use the RAG tool to search for similar transactions
3. Analyze the results and decide if you can answer the user's question
4. Return a structured response

If the similarity score of transactions is less than 0.7 or there are no results - respond that you cannot answer.
If relevant transactions are found - return them in a structured format.

Respond ONLY in JSON format:
{
  "can_answer": true/false,
  "reasoning": "why you can or cannot answer",
  "data": [...] or null,
  "message": "brief description of results"
}"""
    
    def process_task(self, task: str, user_id: int, context: str = "") -> Dict[str, Any]:
        """
        Process a task that requires similarity search using LLM analysis.
        
        Args:
            task: Description of transaction to find similar ones
            user_id: User ID for filtering
            context: Previous conversation context
            
        Returns:
            Dict with similar transactions or indication that no answer found
        """
        logger.info(f"\n{'-'*80}")
        logger.info(f"🔶 RAG AGENT - Processing Task")
        logger.info(f"{'-'*80}")
        logger.info(f"Task: {task}")
        logger.info(f"User ID: {user_id}")
        
        # Extract search query from task
        search_query = self._extract_search_query(task)
        
        logger.info(f"\n🔍 Query Extraction:")
        logger.info(f"Original task: {task}")
        logger.info(f"Extracted search query: '{search_query}'")
        
        if not search_query:
            logger.warning("  ⚠️  Could not extract search query")
            return {
                "success": False,
                "message": "Could not determine which transactions to search for."
            }
        
        # Search for similar transactions using tool
        logger.info(f"\n[EXEC] Calling RAG Tool...")
        logger.info(f"Search query: '{search_query}'")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Top K: 3")
        
        tool_result = self.tool.search_similar(search_query, user_id, top_k=3)
        
        logger.info(f"\n📦 RAG Tool Response:")
        logger.info(f"Success: {'[OK] YES' if tool_result['success'] else '[NO] NO'}")
        
        if not tool_result["success"]:
            logger.error(f"[NO] RAG tool failed: {tool_result.get('error')}")
            return {
                "success": False,
                "message": f"Error searching for similar transactions: {tool_result.get('error', 'Unknown')}"
            }
        
        # Log the similar transactions found
        similar_transactions = tool_result.get('data', [])
        logger.info(f"Similar transactions found: {len(similar_transactions)}")
        if similar_transactions:
            logger.info(f"\n[DATA] Similar Transactions Details:")
            for idx, txn in enumerate(similar_transactions, 1):
                logger.info(f"\n  Transaction {idx}:")
                logger.info(f"    Similarity: {txn.get('similarity_score', 0):.4f}")
                logger.info(f"    Description: {txn.get('description', 'N/A')}")
                logger.info(f"    Amount: {txn.get('amount', 'N/A')}")
                logger.info(f"    Date: {txn.get('transaction_date', 'N/A')}")
        
        # Use LLM to analyze if results can answer the question
        user_prompt = f"""User's task: {task}
        
RAG Tool results (similarity search):
{json.dumps(tool_result, ensure_ascii=False, indent=2)}

Analyze whether these results can answer the user's question.
Remember: only accept transactions with similarity_score > 0.7"""
        
        try:
            logger.info("  [LLM] Analyzing results with LLM...")
            llm_response = call_llm(self.system_prompt, user_prompt, temperature=0.3)
            analysis = json.loads(llm_response)
            logger.info(f"  LLM analysis: can_answer={analysis.get('can_answer')}")
            
            if not analysis.get("can_answer", False):
                return {
                    "success": False,
                    "message": analysis.get("reasoning", "Could not find relevant transactions."),
                    "tool_data": tool_result.get("data", [])
                }
            
            return {
                "success": True,
                "data": analysis.get("data", tool_result.get("data", [])),
                "query": search_query,
                "message": analysis.get("message", ""),
                "reasoning": analysis.get("reasoning", ""),
                "tool_data": tool_result.get("data", [])
            }
            
        except json.JSONDecodeError as e:
            # Fallback if LLM doesn't return valid JSON
            logger.warning(f"  ⚠️  JSON decode failed: {e}, using rule-based filtering")
            similar_transactions = tool_result.get("data", [])
            relevant = [t for t in similar_transactions if t.get("similarity_score", 0) > 0.7]
            
            logger.info(f"  Filtered {len(similar_transactions)} -> {len(relevant)} transactions (score > 0.7)")
            
            if not relevant:
                logger.warning("  ⚠️  No relevant transactions after filtering")
                return {
                    "success": False,
                    "message": "Found transactions are not similar enough to your query."
                }
            
            logger.info(f"  [OK] Success with {len(relevant)} relevant results")
            return {
                "success": True,
                "data": relevant,
                "query": search_query,
                "message": self._format_results(relevant)
            }
        except Exception as e:
            logger.error(f"  [NO] Unexpected error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error analyzing results: {str(e)}"
            }
    
    def _extract_search_query(self, task: str) -> str:
        """Extract search query from task description."""
        remove_words = [
            # English stop words
            "find", "show", "search", "similar", "transactions", "to", "for", "like",
            "payment", "of", "the", "a", "an", "my", "me", "matching", "related",
            "comparable", "same", "analogous"
        ]
        
        words = task.lower().split()
        query_words = [w for w in words if w not in remove_words]
        
        extracted = " ".join(query_words) if query_words else task
        logger.debug(f"  Query extraction: '{task}' -> '{extracted}'")
        
        return extracted
    
    def _format_results(self, transactions: list) -> str:
        """Format similar transactions into readable text."""
        if not transactions:
            return "No similar transactions found"
        
        formatted = f"Found {len(transactions)} similar transactions:\n"
        
        for i, transaction in enumerate(transactions, 1):
            receiver = transaction.get("receiver_name", "Unknown")
            amount = transaction.get("amount", 0)
            text = transaction.get("transaction_text", "")
            similarity = transaction.get("similarity_score", 0)
            
            formatted += f"{i}. {receiver} - {amount} PLN\n"
            formatted += f"   Description: {text}\n"
            formatted += f"   Similarity: {similarity*100:.0f}%\n"
        
        return formatted
from typing import Dict, Any
import json
import logging
from .sql_agent import SQLAgent
from .rag_agent import RAGAgent
from ...chatbot.llm import call_llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MainAgent:
    """
    Main orchestrator agent that coordinates SQL and RAG agents.
    Uses LLM to classify intent and generate user-friendly responses.
    """
    
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
        self.name = "Main Agent"
        self.system_prompt = """You are the main agent of a banking chatbot designed for neurodivergent users, following Web Content Accessibility Guidelines (WCAG).

You have two sub-agents:
1. SQL Agent - for database queries about transactions (balance, history, amounts, etc.)
2. RAG Agent - for finding similar transactions using semantic search

Your tasks:
1. Analyze the user's question
2. Determine which agents are needed (sql, rag, or both)
3. Collect data from agents
4. Generate a clear, simple response

RESPONSE GUIDELINES:
- Answer the user's question directly and simply
- Use plain, clear language - avoid banking jargon
- Keep sentences short (15-20 words max)
- Be specific and direct
- Use **bold** markdown for the most important information (like amounts, names, dates)
- If showing transaction details, just state the facts simply
- No emojis or special characters
- Plain text only, but you can use **bold** markdown

If no agent could find an answer - say: "I couldn't find that information. Try rephrasing your question or adding more details."
"""
    
    def process_query(
        self, 
        user_message: str, 
        user_id: int, 
        conversation_context: str = ""
    ) -> Dict[str, Any]:
        """
        Process user query and generate response.
        
        Args:
            user_message: User's question/request
            user_id: User ID
            conversation_context: Previous conversation history
            
        Returns:
            Dict with response message and metadata
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[TARGET] MAIN AGENT - NEW REQUEST")
        logger.info(f"{'='*80}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"User Query: {user_message}")
        if conversation_context:
            logger.info(f"Context: {conversation_context[:200]}...")
        logger.info(f"{'='*80}\n")
        
        # Determine which agents to use
        needs_sql, needs_rag = self._classify_intent(user_message)
        
        logger.info(f"\n[INFO] INTENT CLASSIFICATION")
        logger.info(f"{'-'*80}")
        logger.info(f"SQL Agent needed: {'[OK] YES' if needs_sql else '[NO] NO'}")
        logger.info(f"RAG Agent needed: {'[OK] YES' if needs_rag else '[NO] NO'}")
        logger.info(f"{'-'*80}\n")
        
        collected_data = {
            "sql_results": None,
            "rag_results": None,
            "tools_used": []
        }
        
        # Execute SQL agent if needed
        if needs_sql:
            logger.info(f"\n[TOOL] CALLING SQL AGENT")
            logger.info(f"{'-'*80}")
            sql_result = self.sql_agent.process_task(
                user_message, user_id, conversation_context
            )
            logger.info(f"\n[DATA] SQL AGENT RESULT:")
            logger.info(f"Success: {'[OK] YES' if sql_result['success'] else '[NO] NO'}")
            if sql_result["success"]:
                collected_data["sql_results"] = sql_result
                collected_data["tools_used"].append("sql")
                data = sql_result.get('data', [])
                data_count = len(data) if data else 0
                logger.info(f"Data records returned: {data_count}")
                if data_count > 0 and isinstance(data, list):
                    sample_data = data[:2]
                    logger.info(f"Sample data: {json.dumps(sample_data, indent=2, ensure_ascii=False)}")
            else:
                logger.warning(f"SQL Agent failed: {sql_result.get('message', 'Unknown error')}")
            logger.info(f"{'-'*80}\n")
        
        # Execute RAG agent if needed
        if needs_rag:
            logger.info(f"\n🔶 CALLING RAG AGENT")
            logger.info(f"{'-'*80}")
            rag_result = self.rag_agent.process_task(
                user_message, user_id, conversation_context
            )
            logger.info(f"\n[DATA] RAG AGENT RESULT:")
            logger.info(f"Success: {'[OK] YES' if rag_result['success'] else '[NO] NO'}")
            if rag_result["success"]:
                collected_data["rag_results"] = rag_result
                collected_data["tools_used"].append("rag")
                similar_count = len(rag_result.get('data', []))
                logger.info(f"Similar transactions found: {similar_count}")
                if similar_count > 0:
                    for idx, item in enumerate(rag_result.get('data', [])[:3], 1):
                        similarity = item.get('similarity_score', 0)
                        description = item.get('description', 'N/A')
                        logger.info(f"  {idx}. Similarity: {similarity:.3f} - {description[:100]}")
            else:
                logger.warning(f"RAG Agent failed: {rag_result.get('message', 'Unknown error')}")
            logger.info(f"{'-'*80}\n")
        
        # Generate final response
        logger.info(f"\n[MSG] GENERATING FINAL RESPONSE")
        logger.info(f"{'-'*80}")
        final_response = self._generate_response(
            user_message, 
            collected_data, 
            conversation_context
        )
        
        logger.info(f"\n[OK] MAIN AGENT COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Success: {final_response.get('success')}")
        logger.info(f"Tools used: {collected_data['tools_used']}")
        logger.info(f"Response preview: {final_response.get('message', '')[:200]}...")
        logger.info(f"{'='*80}\n\n")
        
        return final_response
    
    def _classify_intent(self, message: str) -> tuple[bool, bool]:
        """
        Use LLM to classify user intent and determine which agents to use.
        
        Returns:
            (needs_sql, needs_rag) tuple
        """
        classification_prompt = f"""Analyze the user's question and determine which agents are needed.

Question: {message}

Respond ONLY in JSON format:
{{
  "needs_sql": true/false,
  "needs_rag": true/false,
  "reasoning": "explanation"
}}

SQL needed for: balance, transaction history, amounts, dates, filters
RAG needed for: finding similar transactions, semantic search"""
        
        try:
            logger.info(f"\n[LLM] Calling LLM for Intent Classification")
            logger.info(f"Temperature: 0.3")
            
            llm_response = call_llm(self.system_prompt, classification_prompt, temperature=0.3, log_prompts=True)
            
            logger.info(f"[RECV] LLM Response received")
            logger.info(f"Response: {llm_response[:200]}...")
            
            classification = json.loads(llm_response)
            
            needs_sql = classification.get("needs_sql", False)
            needs_rag = classification.get("needs_rag", False)
            
            logger.info(f"[OK] Classification parsed successfully")
            
            return needs_sql, needs_rag
            
        except json.JSONDecodeError as e:
            logger.error(f"[NO] LLM returned invalid JSON: {e}")
            logger.error(f"Raw response: {llm_response if 'llm_response' in locals() else 'No response'}")
            # Default to SQL for general queries
            return True, False
            
        except Exception as e:
            logger.error(f"[NO] LLM classification error: {e}")
            # Default to SQL for general queries
            return True, False
    
    def _generate_response(
        self, 
        user_message: str, 
        collected_data: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """Generate friendly final response using LLM based on collected data."""
        sql_results = collected_data.get("sql_results")
        rag_results = collected_data.get("rag_results")
        tools_used = collected_data.get("tools_used", [])
        
        # Check if we have any useful data
        has_data = (sql_results and sql_results.get("success")) or \
                   (rag_results and rag_results.get("success"))
        
        if not has_data:
            return {
                "success": False,
                "message": self._generate_no_answer_response(user_message),
                "tools_used": tools_used,
                "metadata": {"data_found": False}
            }
        
        # Use LLM to generate final user-friendly response
        response_prompt = f"""User's question: {user_message}

Conversation context:
{context}

Collected data:

SQL Agent results:
{json.dumps(sql_results, ensure_ascii=False, indent=2) if sql_results else 'Not used'}

RAG Agent results:
{json.dumps(rag_results, ensure_ascii=False, indent=2) if rag_results else 'Not used'}

Answer the user's question directly and simply:

- Use plain, clear language - avoid banking jargon
- Keep sentences short (15-20 words max)
- Be specific and direct
- Use **bold** markdown for the most important information (amounts, names, dates, key facts)
- Just state the facts - no extra formatting or headings
- If showing transaction details, list them simply
- No emojis or special characters
- Plain text only, but you can use **bold** markdown"""
        
        try:
            final_message = call_llm(self.system_prompt, response_prompt, temperature=0.7)
            
            logger.info("  [OK] Successfully generated final response")
            
            return {
                "success": True,
                "message": final_message,
                "tools_used": tools_used,
                "metadata": {
                    "data_found": True,
                    "sql_count": len(sql_results.get("data", [])) if sql_results and isinstance(sql_results.get("data"), list) else 0,
                    "rag_count": len(rag_results.get("data", [])) if rag_results and isinstance(rag_results.get("data"), list) else 0
                }
            }
        except Exception as e:
            # Fallback to simple response
            logger.warning(f"  ⚠️  LLM response generation failed: {e}, using fallback")
            response_parts = []
            
            response_parts.append(self._generate_greeting(user_message))
            
            if sql_results and sql_results.get("success"):
                response_parts.append(sql_results.get("message", ""))
            
            if rag_results and rag_results.get("success"):
                response_parts.append("\n" + rag_results.get("message", ""))
            
            response_parts.append(self._generate_suggestion())
            
            final_message = "\n\n".join(filter(None, response_parts))
            
            logger.info("  [OK] Fallback response generated")
            
            return {
                "success": True,
                "message": final_message,
                "tools_used": tools_used,
                "metadata": {
                    "data_found": True,
                    "sql_count": len(sql_results.get("data", [])) if sql_results else 0,
                    "rag_count": len(rag_results.get("data", [])) if rag_results else 0
                }
            }
    
    def _generate_greeting(self, message: str) -> str:
        """Generate friendly greeting based on query type."""
        greetings = [
            "Sure, I'll help! ",
            "Here's what I found:",
            "Let me check...",
            "Yes, I have information for you:"
        ]
        
        import random
        return random.choice(greetings)
    
    def _generate_no_answer_response(self, message: str) -> str:
        """Generate WCAG-compliant response when no data found."""
        return (
            "I couldn't find that information.\n\n"
            "Here are some ways to ask questions:\n\n"
            "• Show my recent transactions\n"
            "• How much did I spend last month?\n"
            "• Find similar payments to the last one\n\n"
            "Try rephrasing your question or adding more details."
        )
    
    def _generate_suggestion(self) -> str:
        """Generate helpful suggestion for user."""
        suggestions = [
            "Need additional information? Just ask! [MSG]",
            "I can show more details if needed.",
            "Do you need anything else clarified?",
            ""
        ]
        
        import random
        return random.choice(suggestions)
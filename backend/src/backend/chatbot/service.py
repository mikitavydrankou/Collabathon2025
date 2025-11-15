"""
Chatbot service orchestrating the workflow with state management.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from .agents import MainAgent, SuggestionAgent, SuggestionVerifierAgent
from .mcp_client import MCPClient
from .schemas import (
    ChatbotMessageResponse,
    ChatbotStage,
    ChatbotState,
    SuggestionInfo,
    TransactionData,
)
from .logger import logger


class ChatbotService:
    """
    Service managing chatbot conversations and workflow.

    For simplicity, using in-memory session storage.
    In production, use Redis or database.
    """

    # In-memory session storage
    sessions: Dict[str, ChatbotState] = {}

    @classmethod
    def create_session(cls, user_id: int) -> ChatbotState:
        """Create a new chatbot session."""
        session_id = str(uuid.uuid4())
        state = ChatbotState(
            session_id=session_id,
            user_id=user_id,
            stage=ChatbotStage.INITIAL,
        )
        cls.sessions[session_id] = state
        logger.info(f"📝 Created new chatbot session: {session_id} for user {user_id}")
        return state

    @classmethod
    def get_session(cls, session_id: str) -> Optional[ChatbotState]:
        """Get session by ID."""
        return cls.sessions.get(session_id)

    @classmethod
    def update_session(cls, state: ChatbotState) -> None:
        """Update session state."""
        state.updated_at = datetime.utcnow()
        cls.sessions[state.session_id] = state

    @classmethod
    def start_conversation(cls, user_id: int) -> ChatbotMessageResponse:
        """Start a new conversation."""
        state = cls.create_session(user_id)
        return ChatbotMessageResponse(
            session_id=state.session_id,
            stage=ChatbotStage.INITIAL,
            message="Hi! I can help you make a payment. Would you like to see a suggestion based on your past payments?",
            buttons=["yes", "no"],
            transaction_data=state.transaction_data,
        )

    @classmethod
    def handle_message(
        cls, session_id: str, message: Optional[str], action: Optional[str]
    ) -> ChatbotMessageResponse:
        """
        Handle user message or action.

        Args:
            session_id: Session ID
            message: User text message
            action: Button action (yes/no/accept/decline/continue)

        Returns:
            ChatbotMessageResponse
        """
        logger.info(f"📨 Handling message for session {session_id}")
        logger.info(f"   Message: {message or 'None'}")
        logger.info(f"   Action: {action or 'None'}")
        
        state = cls.get_session(session_id)
        if not state:
            logger.warning(f"   ❌ Session not found: {session_id}")
            return ChatbotMessageResponse(
                session_id=session_id,
                stage=ChatbotStage.INITIAL,
                message="Session not found. Please start a new conversation.",
                buttons=None,
            )
        
        logger.info(f"   Current stage: {state.stage}")
        logger.info(f"   User ID: {state.user_id}")

        # Handle based on current stage
        if state.stage == ChatbotStage.INITIAL:
            return cls._handle_initial_stage(state, action)

        elif state.stage == ChatbotStage.FIRST_SUGGESTION:
            return cls._handle_first_suggestion_response(state, action)

        elif state.stage == ChatbotStage.FILTER_SUGGESTION:
            return cls._handle_filter_suggestion_response(state, action)

        elif state.stage in [
            ChatbotStage.COLLECTING_FIELD_1,
            ChatbotStage.COLLECTING_FIELD_2,
            ChatbotStage.COLLECTING_FIELD_3,
            ChatbotStage.COLLECTING_FIELD_4,
        ]:
            return cls._handle_field_collection(state, message)

        elif state.stage == ChatbotStage.FINAL_CHECK:
            return cls._handle_final_check_response(state, action)

        else:
            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Something went wrong. Please start over.",
                buttons=None,
            )

    @classmethod
    def _handle_initial_stage(cls, state: ChatbotState, action: Optional[str]) -> ChatbotMessageResponse:
        """Handle initial stage: want suggestion?"""
        if action == "yes":
            logger.info(f"   ✅ User wants suggestion, fetching first suggestions...")
            # Get first suggestions from MCP
            result = MCPClient.get_first_suggestions(state.user_id)

            # Use SuggestionAgent to pick best one
            suggestion = SuggestionAgent.pick_best_first_suggestion(
                result.transactions, result.user_balance
            )

            if suggestion:
                logger.info(f"   ➡️  Transitioning to FIRST_SUGGESTION stage")
                state.stage = ChatbotStage.FIRST_SUGGESTION
                state.first_suggestion = suggestion  # Store to avoid duplicate in filter suggestion
                cls.update_session(state)

                return ChatbotMessageResponse(
                    session_id=state.session_id,
                    stage=state.stage,
                    message=f"{suggestion.reason}\n\nWould you like to use this payment?",
                    buttons=["accept", "decline"],
                    suggestion=suggestion,
                    transaction_data=state.transaction_data,
                )
            else:
                # No suggestions, go to main flow
                state.stage = ChatbotStage.COLLECTING_FIELD_1
                cls.update_session(state)

                return ChatbotMessageResponse(
                    session_id=state.session_id,
                    stage=state.stage,
                    message="I don't have any suggestions right now. Let's collect the payment details.\n\n"
                    + MainAgent.get_field_prompt(1),
                    buttons=None,
                    transaction_data=state.transaction_data,
                )

        elif action == "no":
            logger.info(f"   ✅ User declined suggestion, starting field collection")
            # Go straight to field collection
            state.stage = ChatbotStage.COLLECTING_FIELD_1
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Okay! Let's collect the payment details.\n\n"
                + MainAgent.get_field_prompt(1),
                buttons=None,
                transaction_data=state.transaction_data,
            )

        return ChatbotMessageResponse(
            session_id=state.session_id,
            stage=state.stage,
            message="Please choose an option.",
            buttons=["yes", "no"],
            transaction_data=state.transaction_data,
        )

    @classmethod
    def _handle_first_suggestion_response(cls, state: ChatbotState, action: Optional[str]) -> ChatbotMessageResponse:
        """Handle response to first suggestion."""
        if action == "accept":
            # User accepted suggestion - go to payment confirmation
            state.stage = ChatbotStage.COMPLETED
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Great! Please review and confirm your payment.",
                buttons=None,
                show_confirm_payment=True,
                transaction_data=state.transaction_data,
            )

        elif action == "decline":
            # User declined - go to main flow
            state.stage = ChatbotStage.COLLECTING_FIELD_1
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="No problem! Let's collect the payment details.\n\n"
                + MainAgent.get_field_prompt(1),
                buttons=None,
                transaction_data=state.transaction_data,
            )

        return ChatbotMessageResponse(
            session_id=state.session_id,
            stage=state.stage,
            message="Please choose an option.",
            buttons=["accept", "decline"],
            transaction_data=state.transaction_data,
        )

    @classmethod
    def _handle_field_collection(cls, state: ChatbotState, message: Optional[str]) -> ChatbotMessageResponse:
        """Handle field collection stages."""
        if not message:
            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Please provide the information.",
                buttons=None,
                transaction_data=state.transaction_data,
            )

        # Determine which field we're collecting
        field_number = {
            ChatbotStage.COLLECTING_FIELD_1: 1,
            ChatbotStage.COLLECTING_FIELD_2: 2,
            ChatbotStage.COLLECTING_FIELD_3: 3,
            ChatbotStage.COLLECTING_FIELD_4: 4,
        }[state.stage]

        # Validate field
        logger.info(f"   🔍 Validating field {field_number} ({MainAgent.FIELD_NAMES[field_number]})")
        is_valid, error_msg, processed_value = MainAgent.validate_and_store_field(
            field_number, message
        )

        if not is_valid:
            logger.warning(f"   ❌ Field validation failed: {error_msg}")
            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message=f"{error_msg}\n\n{MainAgent.get_field_prompt(field_number)}",
                buttons=None,
                transaction_data=state.transaction_data,
            )

        # Store the field
        field_name = MainAgent.FIELD_NAMES[field_number]
        setattr(state.transaction_data, field_name, processed_value)
        logger.info(f"   ✅ Field {field_number} validated and stored: {processed_value}")

        # Check for filter suggestion (only once, and only if we have 2+ fields)
        fields_collected = sum(
            1
            for f in [
                state.transaction_data.recipient_account,
                state.transaction_data.recipient_name,
                state.transaction_data.amount,
                state.transaction_data.transaction_text,
            ]
            if f is not None
        )

        filter_suggestion = None
        if not state.filter_suggestion_shown and fields_collected >= 2:
            logger.info(f"🔄 Session {state.session_id}: Checking for filter suggestion (fields collected: {fields_collected})")
            filter_suggestion = SuggestionVerifierAgent.check_for_suggestion(
                user_id=state.user_id,
                recipient_account=state.transaction_data.recipient_account,
                recipient_name=state.transaction_data.recipient_name,
                amount=state.transaction_data.amount,
                transaction_text=state.transaction_data.transaction_text,
                exclude_suggestion=state.first_suggestion,  # Don't suggest same transaction as first suggestion
            )

        # If we found a confident filter suggestion, show it
        if filter_suggestion:
            logger.info(f"   ✅ Filter suggestion found! Transitioning to FILTER_SUGGESTION stage")
            state.filter_suggestion_shown = True
            state.stage = ChatbotStage.FILTER_SUGGESTION
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message=f"I found a matching payment!\n\n{filter_suggestion.reason}\n\nWould you like to use this?",
                buttons=["accept", "decline"],
                suggestion=filter_suggestion,
                transaction_data=state.transaction_data,
            )

        # Move to next field or final check
        if field_number < 4:
            # Move to next field
            next_stage = {
                1: ChatbotStage.COLLECTING_FIELD_2,
                2: ChatbotStage.COLLECTING_FIELD_3,
                3: ChatbotStage.COLLECTING_FIELD_4,
            }[field_number]
            state.stage = next_stage
            cls.update_session(state)
            logger.info(f"   ➡️  Moving to next stage: {next_stage}")

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message=f"Got it!\n\n{MainAgent.get_field_prompt(field_number + 1)}",
                buttons=None,
                transaction_data=state.transaction_data,
            )
        else:
            # All fields collected - run final check
            logger.info("   ✅ All fields collected, running final check...")
            return cls._run_final_check(state)

    @classmethod
    def _handle_filter_suggestion_response(cls, state: ChatbotState, action: Optional[str]) -> ChatbotMessageResponse:
        """Handle response to filter suggestion."""
        if action == "accept":
            # User accepted suggestion - go to payment confirmation
            state.stage = ChatbotStage.COMPLETED
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Great! Please review and confirm your payment.",
                buttons=None,
                show_confirm_payment=True,
                transaction_data=state.transaction_data,
            )

        elif action == "decline":
            # User declined - continue with field collection
            # Figure out which field to ask for next
            if state.transaction_data.recipient_account is None:
                state.stage = ChatbotStage.COLLECTING_FIELD_1
                field_num = 1
            elif state.transaction_data.recipient_name is None:
                state.stage = ChatbotStage.COLLECTING_FIELD_2
                field_num = 2
            elif state.transaction_data.amount is None:
                state.stage = ChatbotStage.COLLECTING_FIELD_3
                field_num = 3
            else:
                state.stage = ChatbotStage.COLLECTING_FIELD_4
                field_num = 4

            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message=f"No problem! Let's continue.\n\n{MainAgent.get_field_prompt(field_num)}",
                buttons=None,
                transaction_data=state.transaction_data,
            )

        return ChatbotMessageResponse(
            session_id=state.session_id,
            stage=state.stage,
            message="Please choose an option.",
            buttons=["accept", "decline"],
            transaction_data=state.transaction_data,
        )

    @classmethod
    def _run_final_check(cls, state: ChatbotState) -> ChatbotMessageResponse:
        """Run final validation check."""
        logger.info(f"🔍 Running final validation check for session {state.session_id}")
        is_ok, problems = MainAgent.validate_complete_transaction(
            user_id=state.user_id,
            recipient_account=state.transaction_data.recipient_account,
            recipient_name=state.transaction_data.recipient_name,
            amount=state.transaction_data.amount,
            transaction_text=state.transaction_data.transaction_text,
        )

        if is_ok:
            logger.info(f"   ✅ Final check passed, transitioning to COMPLETED stage")
            # Everything is good - go to completion
            state.stage = ChatbotStage.COMPLETED
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Everything looks good! Please review and confirm your payment.",
                buttons=None,
                show_confirm_payment=True,
                transaction_data=state.transaction_data,
            )
        else:
            logger.warning(f"   ⚠️  Final check found problems, transitioning to FINAL_CHECK stage")
            # There are problems - ask user
            state.stage = ChatbotStage.FINAL_CHECK
            state.validation_problems = problems
            state.awaiting_problem_response = True
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message=MainAgent.format_problems_message(problems),
                buttons=["continue", "cancel"],
                validation_problems=problems,
                transaction_data=state.transaction_data,
            )

    @classmethod
    def _handle_final_check_response(cls, state: ChatbotState, action: Optional[str]) -> ChatbotMessageResponse:
        """Handle response to validation problems."""
        if action == "continue":
            # User wants to continue despite problems
            state.stage = ChatbotStage.COMPLETED
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Okay. Please review and confirm your payment.",
                buttons=None,
                show_confirm_payment=True,
                transaction_data=state.transaction_data,
            )

        elif action == "cancel":
            # User wants to cancel
            state.stage = ChatbotStage.INITIAL
            state.transaction_data = TransactionData()
            state.filter_suggestion_shown = False
            state.awaiting_problem_response = False
            state.validation_problems = []
            cls.update_session(state)

            return ChatbotMessageResponse(
                session_id=state.session_id,
                stage=state.stage,
                message="Payment cancelled. Would you like to start over?",
                buttons=["yes", "no"],
                transaction_data=state.transaction_data,
            )

        return ChatbotMessageResponse(
            session_id=state.session_id,
            stage=state.stage,
            message="Please choose an option.",
            buttons=["continue", "cancel"],
            validation_problems=state.validation_problems,
            transaction_data=state.transaction_data,
        )

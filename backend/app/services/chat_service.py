
import logging

from sqlalchemy.orm import Session

from app.ai.service import AIService, AIServiceError

from app.services.conversation_service import (
    get_conversation,
    get_conversation_messages,
    add_message,
)

from app.services.memory_service import (
    process_memory,
    get_memory_type_from_message,
    get_relevant_memory,
    is_memory_question,
)


logger = logging.getLogger("miraidesk.chat")


class ChatService:

    def __init__(self):
        self.ai_service = AIService()

    def chat(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
        message: str,
    ):

        # Verify conversation ownership.
        conversation = get_conversation(
            db,
            conversation_id,
            user_id,
        )

        if not conversation:
            return None

        # Load existing history before processing this message.
        history = get_conversation_messages(
            db,
            conversation_id,
        )

        # Process and retrieve memories.
        memories = []
        memory_question = is_memory_question(message)

        if not memory_question:
            processed_memory = process_memory(
                db,
                user_id,
                message,
            )

            if processed_memory:
                memories = [processed_memory]

        if memory_question:
            memory_type = get_memory_type_from_message(message)

            if memory_type:
                relevant_memory = get_relevant_memory(
                    db,
                    user_id,
                    memory_type,
                )

                if relevant_memory:
                    memories = [relevant_memory]

        # Generate the AI response before saving either chat message.
        # If Gemini fails, no new chat messages have been added.
        ai_response = self.ai_service.generate_response(
            message,
            history,
            memories,
        )

        # Save both messages in one database transaction.
        try:
            user_message = add_message(
                db,
                conversation_id,
                "user",
                message,
                commit=False,
            )

            assistant_message = add_message(
                db,
                conversation_id,
                "assistant",
                ai_response,
                commit=False,
            )

            db.commit()

            # Refresh after the shared transaction commits.
            db.refresh(user_message)
            db.refresh(assistant_message)

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to save chat messages for conversation_id=%s",
                conversation_id,
            )

            raise

        return {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

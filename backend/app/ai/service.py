import logging
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Raised when the AI provider cannot generate a response."""

    def __init__(
        self,
        message: str,
        status_code: int = 503,
    ):
        super().__init__(message)
        self.status_code = status_code


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================


class AIService:
    """
    Core AI service for MiraiDesk-AI.

    Handles:
    - Basic conversations
    - Conversation history
    - Long-term memories
    - Memory retrieval
    - Context-aware follow-ups
    - General knowledge
    - Gemini AI responses
    """

    def __init__(self):
        # -----------------------------------------------------
        # Gemini configuration
        # -----------------------------------------------------

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite"
        )

        self.client = None

        if (
            self.api_key
            and self.api_key.strip()
        ):
            try:
                self.client = genai.Client(
                    api_key=self.api_key
                )

                print(
                    f"[MiraiDesk-AI] Gemini client initialized."
                )
                print(
                    f"[MiraiDesk-AI] Model: {self.model}"
                )

            except Exception as error:
                print(
                    "\n[MiraiDesk-AI] ERROR: "
                    "Could not initialize Gemini client."
                )
                print(
                    f"Error: {error}"
                )

    # =========================================================
    # MAIN RESPONSE
    # =========================================================

    def generate_response(
        self,
        message: str,
        conversation_history=None,
        memories=None
    ) -> str:

        if not message or not message.strip():
            return "Please provide a message."

        message = message.strip()

        if conversation_history is None:
            conversation_history = []

        if memories is None:
            memories = []

        message_lower = message.lower()

        # -----------------------------------------------------
        # FORMAT DATA
        # -----------------------------------------------------

        history_data = self.format_conversation_history(
            conversation_history
        )

        memory_data = self.format_memories(
            memories
        )

        recent_user_messages = (
            self.get_recent_user_messages(
                history_data
            )
        )

        # -----------------------------------------------------
        # BASIC RESPONSES
        # -----------------------------------------------------

        basic_response = self.get_basic_response(
            message_lower
        )

        if basic_response:
            return basic_response

        # -----------------------------------------------------
        # MEMORY STATEMENTS
        # -----------------------------------------------------

        memory_statement = self.detect_memory_statement(
            message,
            message_lower
        )

        if memory_statement:
            return memory_statement

        # -----------------------------------------------------
        # MEMORY QUESTIONS
        # -----------------------------------------------------

        memory_response = self.get_memory_response(
            message_lower,
            memory_data
        )

        if memory_response:
            return memory_response

        # -----------------------------------------------------
        # CONTEXT FOLLOW-UP
        # -----------------------------------------------------

        context_response = self.check_context_follow_up(
            message_lower,
            recent_user_messages
        )

        if context_response:
            return context_response

        # -----------------------------------------------------
        # GENERAL KNOWLEDGE
        # -----------------------------------------------------

        general_response = self.get_general_response(
            message_lower
        )

        if general_response:
            return general_response

        # -----------------------------------------------------
        # GEMINI AI
        # -----------------------------------------------------

        ai_response = self.generate_ai_response(
            message=message,
            history_data=history_data,
            memory_data=memory_data
        )

        if ai_response:
            return ai_response

        # Never return fallback text as if Gemini succeeded.
        raise AIServiceError(
            "The AI provider could not generate a response.",
            status_code=503,
        )

    # =========================================================
    # BASIC RESPONSES
    # =========================================================

    def get_basic_response(self, message_lower):

        if (
            message_lower == "hello"
            or message_lower == "hi"
            or message_lower.startswith("hello ")
            or message_lower.startswith("hi ")
        ):
            return (
                "Hello Senpai! 👋 I'm MiraiDesk-AI. "
                "How can I help you today?"
            )

        if "who are you" in message_lower:
            return (
                "I'm MiraiDesk-AI, your AI-powered "
                "desktop assistant."
            )

        if "what is miraidesk" in message_lower:
            return (
                "MiraiDesk-AI is an AI assistant project "
                "with authentication, conversations, "
                "message history, long-term memory, "
                "context awareness, and AI capabilities."
            )

        if "how are you" in message_lower:
            return (
                "I'm doing great, Senpai! 🚀 "
                "Ready to work on MiraiDesk-AI."
            )

        return None

    # =========================================================
    # MEMORY STATEMENTS
    # =========================================================

    def detect_memory_statement(
        self,
        message,
        message_lower
    ):

        # -----------------------------------------------------
        # Favorite language
        # -----------------------------------------------------

        language_patterns = [
            "favorite programming language is",
            "favorite language is",
            "preferred language is",
        ]

        for pattern in language_patterns:

            if pattern in message_lower:

                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                language = (
                    message[start:]
                    .strip()
                    .rstrip(".")
                )

                if language:
                    return (
                        "Got it, Senpai! I'll remember that "
                        "your favorite programming language "
                        f"is {language}."
                    )

        # -----------------------------------------------------
        # Goal
        # -----------------------------------------------------

        goal_patterns = [
            "my goal is",
            "my objective is",
            "i want to achieve",
        ]

        for pattern in goal_patterns:

            if pattern in message_lower:

                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                goal = (
                    message[start:]
                    .strip()
                    .rstrip(".")
                )

                if goal:
                    return (
                        "Got it, Senpai! I'll remember that "
                        f"your goal is {goal}."
                    )

        # -----------------------------------------------------
        # Location
        # -----------------------------------------------------

        location_patterns = [
            "i live in",
            "i am living in",
            "my location is",
        ]

        for pattern in location_patterns:

            if pattern in message_lower:

                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                location = (
                    message[start:]
                    .strip()
                    .rstrip(".")
                )

                if location:
                    return (
                        "Got it, Senpai! I'll remember that "
                        f"you live in {location}."
                    )

        return None

    # =========================================================
    # MEMORY QUESTIONS
    # =========================================================

    def get_memory_response(
        self,
        message_lower,
        memory_data
    ):

        # -----------------------------------------------------
        # Favorite language
        # -----------------------------------------------------

        if (
            "favorite programming language"
            in message_lower
            or "favorite language"
            in message_lower
            or "preferred language"
            in message_lower
            or "language do i like"
            in message_lower
        ):

            if "favorite_language" in memory_data:
                return (
                    "Your favorite programming language "
                    f"is {memory_data['favorite_language']}."
                )

            return (
                "I don't think you've told me your favorite "
                "programming language yet."
            )

        # -----------------------------------------------------
        # Goal
        # -----------------------------------------------------

        if (
            "what is my goal" in message_lower
            or "what am i trying to achieve"
            in message_lower
            or "what do i want to achieve"
            in message_lower
            or "what is my objective"
            in message_lower
        ):

            if "goal" in memory_data:
                return (
                    f"Your goal is {memory_data['goal']}."
                )

            return (
                "I don't think you've told me your goal yet."
            )

        # -----------------------------------------------------
        # Location
        # -----------------------------------------------------

        if (
            "where do i live" in message_lower
            or "where i live" in message_lower
            or "where am i living"
            in message_lower
            or "what is my location"
            in message_lower
            or "where is my home"
            in message_lower
        ):

            if "location" in memory_data:
                return (
                    "You told me that you live in "
                    f"{memory_data['location']}."
                )

            return (
                "I don't think you've told me where you live yet."
            )

        return None

    # =========================================================
    # CONTEXT
    # =========================================================

    def check_context_follow_up(
        self,
        message_lower,
        recent_user_messages
    ):

        if not recent_user_messages:
            return None

        # -----------------------------------------------------
        # Favorite language follow-up
        # -----------------------------------------------------

        is_language_follow_up = (
            "why is it popular" in message_lower
            or "why is it so popular"
            in message_lower
            or "why is that popular"
            in message_lower
        )

        # -----------------------------------------------------
        # Goal follow-up
        # -----------------------------------------------------

        is_goal_follow_up = (
            "what should i learn first"
            in message_lower
            or "what should i start with"
            in message_lower
            or "where should i start"
            in message_lower
        )

        # -----------------------------------------------------
        # Check recent messages
        # -----------------------------------------------------

        for recent_message in recent_user_messages:

            recent_lower = recent_message.lower()

            # -------------------------------------------------
            # Favorite language context
            # -------------------------------------------------

            if is_language_follow_up:

                if (
                    "favorite programming language is"
                    in recent_lower
                    or "favorite language is"
                    in recent_lower
                    or "preferred language is"
                    in recent_lower
                ):
                    return (
                        "It's popular because it is easy "
                        "to learn, has a large ecosystem, "
                        "and is widely used for web "
                        "development, automation, data "
                        "science, and AI."
                    )

            # -------------------------------------------------
            # Goal context
            # -------------------------------------------------

            if is_goal_follow_up:

                if (
                    "my goal is" in recent_lower
                    or "my objective is"
                    in recent_lower
                    or "i want to achieve"
                    in recent_lower
                ):
                    return (
                        "Since your goal is related to "
                        "becoming an AI engineer, a good "
                        "starting point is Python, followed "
                        "by mathematics, data structures, "
                        "machine learning, and practical "
                        "AI projects. 🚀"
                    )

        return None

    # =========================================================
    # GENERAL KNOWLEDGE
    # =========================================================

    def get_general_response(
        self,
        message_lower
    ):

        if "capital of japan" in message_lower:
            return (
                "The capital of Japan is Tokyo. 🇯🇵"
            )

        if "capital of india" in message_lower:
            return (
                "The capital of India is New Delhi. 🇮🇳"
            )

        if "what is python" in message_lower:
            return (
                "Python is a high-level, general-purpose "
                "programming language known for its simple "
                "syntax and readability. It is widely used "
                "in web development, automation, data science, "
                "machine learning, and artificial intelligence."
            )

        if (
            "what is artificial intelligence"
            in message_lower
            or message_lower == "what is ai"
            or "what is ai?" in message_lower
        ):
            return (
                "Artificial Intelligence (AI) is a field "
                "of computer science focused on creating "
                "systems that can perform tasks that normally "
                "require human intelligence."
            )

        if "what is machine learning" in message_lower:
            return (
                "Machine Learning is a branch of AI where "
                "computers learn patterns from data and use "
                "those patterns to make predictions or decisions."
            )

        return None

    # =========================================================
    # GEMINI AI RESPONSE
    # =========================================================

    def generate_ai_response(
        self,
        message,
        history_data,
        memory_data
    ):
        if not self.api_key or not self.api_key.strip():
            logger.error("Gemini API key is missing.")
            raise AIServiceError(
                "AI service is not configured.",
                status_code=503,
            )

        if self.client is None:
            logger.error("Gemini client is unavailable.")
            raise AIServiceError(
                "AI service is not available.",
                status_code=503,
            )

        instructions = """
You are MiraiDesk-AI, a helpful AI desktop assistant.

Be friendly, accurate, and concise.
The user may be addressed as Senpai.
Use the supplied conversation history and long-term
memory when relevant.
Do not claim that you remember information unless
it is actually present in the supplied context.
Answer general knowledge questions normally.
For programming questions, provide practical and
correct explanations and code when appropriate.
If you are uncertain, clearly say so rather than
inventing facts.
"""

        memory_context = ""
        if memory_data:
            memory_context = "\n\nLONG-TERM USER MEMORY:\n"
            for memory_type, content in memory_data.items():
                memory_context += f"{memory_type}: {content}\n"

        conversation_context = ""
        for item in history_data[-10:]:
            role = item.get("role", "user")
            content = item.get("content", "")
            conversation_context += f"{role}: {content}\n"

        input_text = (
            instructions
            + memory_context
            + "\n\nRECENT CONVERSATION:\n"
            + conversation_context
            + "\n\nCURRENT USER MESSAGE:\n"
            + message
        )

        max_attempts = 3
        transient_statuses = {429, 500, 502, 503, 504}
        permanent_statuses = {400, 401, 403, 404}

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    "Calling Gemini model %s (attempt %d/%d).",
                    self.model,
                    attempt,
                    max_attempts,
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=input_text,
                )

                answer = response.text
                if answer and answer.strip():
                    logger.info("Gemini response generated successfully.")
                    return answer.strip()

                logger.warning("Gemini returned an empty response.")
                raise AIServiceError(
                    "The AI provider returned an empty response.",
                    status_code=502,
                )

            except AIServiceError:
                raise

            except Exception as error:
                from google.genai import errors as genai_errors

                raw_status = getattr(error, "code", None)
                if raw_status is None:
                    raw_status = getattr(error, "status_code", None)

                try:
                    status = int(raw_status)
                except (TypeError, ValueError):
                    status = None

                status_text = str(getattr(error, "status", "") or "").upper()

                # Authentication and request configuration failures.
                if status in {400, 401, 403, 404} or status_text in {
                    "INVALID_ARGUMENT",
                    "UNAUTHENTICATED",
                    "PERMISSION_DENIED",
                }:
                    logger.error(
                        "Gemini rejected the request (type: %s, status: %s).",
                        type(error).__name__,
                        status if status is not None else "unknown",
                    )
                    raise AIServiceError(
                        "The AI provider rejected the request. Check the API key, model, and configuration.",
                        status_code=502,
                    ) from None

                # Retry only recognized temporary HTTP/API failures.
                is_transient = (
                    isinstance(error, genai_errors.ServerError)
                    or status in {429, 500, 502, 503, 504}
                    or status_text in {
                        "RESOURCE_EXHAUSTED",
                        "UNAVAILABLE",
                        "INTERNAL",
                        "DEADLINE_EXCEEDED",
                    }
                )

                if not is_transient:
                    logger.error(
                        "Gemini request failed (type: %s, status: %s).",
                        type(error).__name__,
                        status if status is not None else "unknown",
                    )
                    raise AIServiceError(
                        "The AI provider request failed.",
                        status_code=502,
                    ) from None

                if attempt >= max_attempts:
                    logger.warning(
                        "Gemini remained temporarily unavailable after %d attempts.",
                        max_attempts,
                    )
                    raise AIServiceError(
                        "The AI provider is temporarily unavailable. Please try again.",
                        status_code=503,
                    ) from None

                delay_seconds = attempt
                logger.warning(
                    "Temporary Gemini failure; retrying in %d second(s) "
                    "(attempt %d/%d).",
                    delay_seconds,
                    attempt,
                    max_attempts,
                )
                time.sleep(delay_seconds)

        raise AIServiceError(
            "The AI provider could not generate a response.",
            status_code=503,
        )

    # =========================================================
    # HISTORY
    # =========================================================

    def format_conversation_history(
        self,
        conversation_history
    ):

        history_data = []

        for history_message in conversation_history:

            history_data.append({
                "role": history_message.role,
                "content": history_message.content
            })

        return history_data

    # =========================================================
    # MEMORIES
    # =========================================================

    def format_memories(
        self,
        memories
    ):

        memory_data = {}

        for memory in memories:

            memory_data[
                memory.memory_type
            ] = memory.content

        return memory_data

    # =========================================================
    # RECENT USER MESSAGES
    # =========================================================

    def get_recent_user_messages(
        self,
        history_data,
        limit=10
    ):

        user_messages = []

        for history_message in reversed(
            history_data
        ):

            if history_message["role"] == "user":

                user_messages.append(
                    history_message["content"]
                )

                if len(user_messages) >= limit:
                    break

        return user_messages
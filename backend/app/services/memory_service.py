from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.core.exceptions import DatabaseException


# =========================================================
# CREATE / UPDATE MEMORY
# =========================================================

def create_memory(
    db: Session,
    user_id: int,
    memory_type: str,
    content: str
):
    """
    Create a new memory or update the user's
    existing memory of the same type.
    """

    if not content or not content.strip():
        return None

    content = content.strip()

    existing_memory = (
        db.query(Memory)
        .filter(
            Memory.user_id == user_id,
            Memory.memory_type == memory_type
        )
        .order_by(
            Memory.created_at.desc()
        )
        .first()
    )

    # Update existing memory
    if existing_memory:
        existing_memory.content = content

        try:
            db.commit()
            db.refresh(existing_memory)

            return existing_memory

        except Exception:
            db.rollback()
            raise DatabaseException()

    # Create new memory
    memory = Memory(
        user_id=user_id,
        memory_type=memory_type,
        content=content
    )

    db.add(memory)

    try:
        db.commit()
        db.refresh(memory)

        return memory

    except Exception:
        db.rollback()
        raise DatabaseException()


# =========================================================
# GET ALL USER MEMORIES
# =========================================================

def get_user_memories(
    db: Session,
    user_id: int
):
    """
    Return all memories belonging to a user.
    """

    return (
        db.query(Memory)
        .filter(
            Memory.user_id == user_id
        )
        .order_by(
            Memory.created_at.desc()
        )
        .all()
    )


# =========================================================
# GET MEMORIES BY TYPE
# =========================================================

def get_memories_by_type(
    db: Session,
    user_id: int,
    memory_type: str
):
    """
    Return all memories of a specific type
    belonging to a user.
    """

    return (
        db.query(Memory)
        .filter(
            Memory.user_id == user_id,
            Memory.memory_type == memory_type
        )
        .order_by(
            Memory.created_at.desc()
        )
        .all()
    )


# =========================================================
# GET RELEVANT MEMORY
# =========================================================

def get_relevant_memory(
    db: Session,
    user_id: int,
    memory_type: str
):
    """
    Return the latest memory of a specific type.
    """

    return (
        db.query(Memory)
        .filter(
            Memory.user_id == user_id,
            Memory.memory_type == memory_type
        )
        .order_by(
            Memory.created_at.desc()
        )
        .first()
    )


# =========================================================
# DETECT MEMORY TYPE
# =========================================================

def get_memory_type_from_message(
    message: str
):
    """
    Detect the memory category from a natural-language message.
    """

    if not message or not message.strip():
        return None

    message_lower = message.lower().strip()

    favorite_language_patterns = [
        "favorite programming language",
        "favourite programming language",
        "favorite language",
        "favourite language",
        "preferred programming language",
        "preferred language",
        "programming language do i like",
        "language do i like",
        "i mainly code in",
        "i mostly code in",
        "i usually code in",
        "i prefer coding in",
        "i love coding in",
        "i like coding in",
        "i code mostly in",
        "i am learning",
        "i'm learning",
        "i am currently learning",
        "i'm currently learning",
        "learning python",
        "learning java",
        "learning c++",
    ]

    if any(
        pattern in message_lower
        for pattern in favorite_language_patterns
    ):
        return "favorite_language"

    goal_patterns = [
        "my goal",
        "my objective",
        "my aim",
        "i want to achieve",
        "i want to become",
        "i'm trying to become",
        "i am trying to become",
        "i'm planning to become",
        "i am planning to become",
        "i'm working towards",
        "i am working towards",
        "what am i trying to achieve",
        "what do i want to achieve",
        "what is my goal",
        "what is my objective",
        "i hope to become",
        "i plan to become",
        "i am pursuing a career as",
        "i'm pursuing a career as",
    ]

    if any(
        pattern in message_lower
        for pattern in goal_patterns
    ):
        return "goal"

    location_patterns = [
        "i live in",
        "i am living in",
        "i'm living in",
        "my location is",
        "i'm from",
        "i am from",
        "my hometown is",
        "i stay in",
        "i'm staying in",
        "i am staying in",
        "where do i live",
        "where i live",
        "where am i living",
        "what is my location",
        "where is my home",
    ]

    if any(
        pattern in message_lower
        for pattern in location_patterns
    ):
        return "location"

    return None


# =========================================================
# EXTRACT MEMORY
# =========================================================

def extract_memory_from_message(
    message: str,
    memory_type: str
):
    """
    Extract the actual memory content from
    the user's message.
    """

    if (
        not message
        or not message.strip()
        or not memory_type
    ):
        return None

    message_lower = message.lower().strip()

    if memory_type == "favorite_language":
        patterns = [
            "my favorite programming language is",
            "my favorite language is",
            "my preferred programming language is",
            "my preferred language is",
            "favorite programming language is",
            "favorite language is",
            "preferred programming language is",
            "preferred language is",
            "i mainly code in",
            "i mostly code in",
            "i usually code in",
            "i prefer coding in",
            "i love coding in",
            "i like coding in",
            "i code mostly in",
            "i am learning",
            "i'm learning",
            "i am currently learning",
            "i'm currently learning",
        ]

        for pattern in patterns:
            if pattern in message_lower:
                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                content = (
                    message[start:]
                    .strip()
                    .rstrip(".!?")
                )

                if content:
                    return content

    if memory_type == "goal":
        patterns = [
            "my goal is",
            "my objective is",
            "my aim is",
            "i want to achieve",
            "i want to become",
            "i'm trying to become",
            "i am trying to become",
            "i'm planning to become",
            "i am planning to become",
            "i'm working towards",
            "i am working towards",
            "i hope to become",
            "i plan to become",
            "i am pursuing a career as",
            "i'm pursuing a career as",
        ]

        for pattern in patterns:
            if pattern in message_lower:
                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                content = (
                    message[start:]
                    .strip()
                    .rstrip(".!?")
                )

                if content:
                    return content

    if memory_type == "location":
        patterns = [
            "i live in",
            "i am living in",
            "i'm living in",
            "my location is",
            "i'm from",
            "i am from",
            "my hometown is",
            "i stay in",
            "i'm staying in",
            "i am staying in",
        ]

        for pattern in patterns:
            if pattern in message_lower:
                start = (
                    message_lower.index(pattern)
                    + len(pattern)
                )

                content = (
                    message[start:]
                    .strip()
                    .rstrip(".!?")
                )

                if content:
                    return content

    return None


# =========================================================
# PROCESS MEMORY
# =========================================================

def process_memory(
    db: Session,
    user_id: int,
    message: str
):
    """
    Process a user message for long-term memory.

    Steps:

    1. Detect memory type.
    2. Extract memory content.
    3. Create or update the memory.
    4. Retrieve the stored memory.
    """

    if not message or not message.strip():
        return None

    memory_type = get_memory_type_from_message(message)

    if not memory_type:
        return None

    memory_content = extract_memory_from_message(
        message,
        memory_type
    )

    if not memory_content:
        return None

    create_memory(
        db=db,
        user_id=user_id,
        memory_type=memory_type,
        content=memory_content
    )

    return get_relevant_memory(
        db=db,
        user_id=user_id,
        memory_type=memory_type
    )


# =========================================================
# DETECT MEMORY QUESTION
# =========================================================

def is_memory_question(
    message: str
):
    """
    Determine whether the user is asking
    about an existing stored memory.
    """

    if not message or not message.strip():
        return False

    message_lower = message.lower().strip()

    memory_question_patterns = [
        "what is my goal",
        "what is my objective",
        "what is my aim",
        "what do i want to achieve",
        "what am i trying to achieve",
        "what am i working towards",

        "what is my favorite language",
        "what is my favourite language",
        "what is my favorite programming language",
        "what is my favourite programming language",
        "which language do i like",
        "which programming language do i like",

        "where do i live",
        "where am i living",
        "what is my location",
        "where is my home",
    ]

    return any(
        pattern in message_lower
        for pattern in memory_question_patterns
    )


# =========================================================
# UPDATE MEMORY
# =========================================================

def update_memory(
    db: Session,
    memory_id: int,
    user_id: int,
    memory_type: str,
    content: str
):
    """
    Update a memory only if it belongs to the current user.
    """

    memory = (
        db.query(Memory)
        .filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        )
        .first()
    )

    if not memory:
        return None

    memory.memory_type = memory_type
    memory.content = content.strip()

    try:
        db.commit()
        db.refresh(memory)

        return memory

    except Exception:
        db.rollback()
        raise DatabaseException()


# =========================================================
# DELETE MEMORY
# =========================================================

def delete_memory(
    db: Session,
    memory_id: int,
    user_id: int
):
    """
    Delete a memory only if it belongs to the current user.
    """

    memory = (
        db.query(Memory)
        .filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        )
        .first()
    )

    if not memory:
        return None

    try:
        db.delete(memory)
        db.commit()

        return memory

    except Exception:
        db.rollback()
        raise DatabaseException()
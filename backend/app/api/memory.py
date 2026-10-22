from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.dependencies.auth import get_current_user
from app.models.user import User

from app.schemas.memory import (
    APIResponse,
    MemoryCreate,
    MemoryResponse,
)

from app.services.memory_service import (
    create_memory,
    get_user_memories,
    get_memories_by_type,
    update_memory,
    delete_memory,
)


router = APIRouter(
    prefix="/memory",
    tags=["Memory"]
)


# --------------------------------------------------
# CREATE MEMORY
# --------------------------------------------------

@router.post(
    "/",
    response_model=APIResponse[MemoryResponse]
)
def create_new_memory(
    memory: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    created_memory = create_memory(
        db=db,
        user_id=current_user.id,
        memory_type=memory.memory_type,
        content=memory.content
    )

    return APIResponse(
        success=True,
        data=created_memory
    )


# --------------------------------------------------
# GET USER MEMORIES
# --------------------------------------------------

@router.get(
    "/user/{user_id}",
    response_model=APIResponse[list[MemoryResponse]]
)
def get_memories(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Memories not found"
        )

    memories = get_user_memories(
        db=db,
        user_id=current_user.id
    )

    return APIResponse(
        success=True,
        data=memories
    )


# --------------------------------------------------
# GET MEMORIES BY TYPE
# --------------------------------------------------

@router.get(
    "/user/{user_id}/{memory_type}",
    response_model=APIResponse[list[MemoryResponse]]
)
def get_memories_type(
    user_id: int,
    memory_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Memories not found"
        )

    memories = get_memories_by_type(
        db=db,
        user_id=current_user.id,
        memory_type=memory_type
    )

    return APIResponse(
        success=True,
        data=memories
    )


# --------------------------------------------------
# UPDATE MEMORY
# --------------------------------------------------

@router.put(
    "/{memory_id}",
    response_model=APIResponse[MemoryResponse]
)
def update_existing_memory(
    memory_id: int,
    memory: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_memory = update_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id,
        memory_type=memory.memory_type,
        content=memory.content
    )

    if not updated_memory:
        raise HTTPException(
            status_code=404,
            detail="Memory not found"
        )

    return APIResponse(
        success=True,
        data=updated_memory
    )


# --------------------------------------------------
# DELETE MEMORY
# --------------------------------------------------

@router.delete(
    "/{memory_id}",
    response_model=APIResponse[MemoryResponse]
)
def delete_existing_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deleted_memory = delete_memory(
        db=db,
        memory_id=memory_id,
        user_id=current_user.id
    )

    if not deleted_memory:
        raise HTTPException(
            status_code=404,
            detail="Memory not found"
        )

    return APIResponse(
        success=True,
        data=deleted_memory
    )
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.database.session import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)
from app.services.user_service import (
    create_user,
    authenticate_user,
)
from app.core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/")
def auth_root():
    return {
        "message": "Authentication API is working!"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy"
    }


@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return create_user(db, user)


@router.post(
    "/login",
    response_model=Token
)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    db_user = authenticate_user(db, user)

    access_token = create_access_token(
        data={
            "sub": db_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.user import UserCreate, UserResponse
from backend.schemas.auth import LoginRequest, Token
from backend.services.user_service import UserService
from backend.security.auth import create_access_token

router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new patient user, including emergency profile, primary doctor, 
    and up to 5 priority contacts.
    """
    db_user = UserService.create_user(db=db, user_data=user_data)
    return db_user


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and returns a JWT access token.
    """
    db_user = UserService.authenticate_user(db=db, login_data=login_data)
    
    # Sign user token
    access_token = create_access_token(data={"sub": db_user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

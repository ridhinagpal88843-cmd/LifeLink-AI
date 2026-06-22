from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserResponse, UserUpdate
from backend.security.auth import get_current_user
from backend.services.user_service import UserService

router = APIRouter(tags=["User Profile"])


@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve current authenticated user's emergency information.
    Requires Bearer authorization token.
    """
    profile = UserService.get_user_profile(db=db, user_id=current_user.id)
    return profile


@router.put("/profile", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Modify current user's profile, emergency clinical details, or contact configurations.
    Validates updated contacts count limits (max 5 items).
    """
    updated_user = UserService.update_user_profile(
        db=db, 
        user_id=current_user.id, 
        update_data=update_data
    )
    return updated_user

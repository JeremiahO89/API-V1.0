from fastapi import APIRouter, Depends
from api.dependents import db_dependency, user_dependency
from api.models import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.get("/me")
async def get_my_user_data(
    current_user: user_dependency,
    db: db_dependency
):
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel, validator
from jose import jwt
from dotenv import load_dotenv
import os
from api.models import User
from api.dependents import db_dependency, bcrypt_context

load_dotenv()

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("AUTH_ALGORITHM")


class UserCreateRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str

    @validator("password")
    def password_min_length(cls, v):
        if len(v) < 2:
            raise ValueError("Password must be at least 8 characters")
        return v

    @validator("first_name", "last_name")
    def names_not_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Name fields cannot be empty")
        return v.strip()


class UserLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: UserCreateRequest):
    existing_user = db.query(User).filter(User.username == create_user_request.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    create_user_model = User(
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
    )
    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return {
        "id": create_user_model.id,
        "username": create_user_model.username,
        "first_name": create_user_model.first_name,
        "last_name": create_user_model.last_name,
    }


@router.post('/token', response_model=Token)
async def login_for_access_token(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: db_dependency
):
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {
        "access_token": token,
        "token_type": "bearer"
    }

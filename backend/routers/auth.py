from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core import config
from core.ratelimit import limiter
from core.security import authenticate_user, create_access_token, get_current_user, get_password_hash
from database import get_db
from models import User
from schemas.auth import Token, UserCreate, UserResponse

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(config.RATE_AUTH)
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(username=user.username, email=user.email, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
@limiter.limit(config.RATE_AUTH)
def login(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.username}, timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    # Cookie httpOnly : inaccessible au JavaScript (donc à un XSS). Le jeton est aussi renvoyé pour Swagger/CLI.
    response.set_cookie(
        key=config.COOKIE_NAME, value=token, httponly=True, secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE, max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(config.COOKIE_NAME, path="/")


@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

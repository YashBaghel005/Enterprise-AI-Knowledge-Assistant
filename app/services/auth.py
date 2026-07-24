from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse


def register_user(db: Session, user_data: UserCreate) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user is not None:
        raise ValueError("Email is already registered")

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def login_user(db: Session, credentials: UserLogin) -> Token:
    user = db.query(User).filter(User.email == credentials.email).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise ValueError("Incorrect email or password")

    if not user.is_active:
        raise ValueError("This account has been deactivated")

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)
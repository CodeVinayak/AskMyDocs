from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .db.database import get_db
from sqlalchemy.orm import Session
from .db import models
from pydantic import BaseModel
import logging # Import logging

logger = logging.getLogger(__name__)

# Configuration for JWT
SECRET_KEY = "YOUR_SUPER_SECRET_KEY" # TODO: Load from environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Example: 30 minutes

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # Default expiration
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# OAuth2PasswordBearer for token extraction from headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") # tokenUrl should point to your login endpoint

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract user ID from token payload (assuming 'sub' claim is used for user ID)
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("JWT payload missing user ID (sub claim).")
            raise credentials_exception
        # Convert user_id to integer if stored as INT in DB
        user_id_int = int(user_id)
        logger.debug(f"Authenticated user ID from token: {user_id_int}")
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}", exc_info=True)
        raise credentials_exception
    except ValueError as e:
        logger.warning(f"Invalid user ID format in JWT payload: {e}", exc_info=True)
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error during JWT decoding: {e}", exc_info=True)
        raise credentials_exception

    # Retrieve user from database
    try:
        user = db.query(models.User).filter(models.User.id == user_id_int).first()
        if user is None:
            logger.warning(f"User with ID {user_id_int} not found in DB.")
            raise credentials_exception
        logger.debug(f"Retrieved user {user.id} from DB.")
        return user
    except SQLAlchemyError as e:
         logger.error(f"Database error retrieving user {user_id_int} for authentication: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during authentication.")
    except Exception as e:
         logger.error(f"Unexpected error retrieving user {user_id_int} for authentication: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during authentication.")

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    email: str
    password: str
    username: str # Assuming username is also required for registration

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserPublic(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True # Enable Pydantic to work with ORM objects 
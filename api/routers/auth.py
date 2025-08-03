"""
Authentication API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..database import get_db
from ..auth import AuthService, get_current_user
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token, TokenRefresh,
    APIKeyCreate, APIKeyResponse, ErrorResponse
)
from ..models import User
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user
    """
    try:
        user = AuthService.create_user(
            db=db,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """
    Login with email/username and password
    """
    # Try to authenticate with email first, then username
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Try username if email failed
        user_by_username = AuthService.get_user_by_username(db, form_data.username)
        if user_by_username:
            if AuthService.verify_password(form_data.password, user_by_username.hashed_password):
                user = user_by_username
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = AuthService.decode_token(token_data.refresh_token)
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        new_refresh_token = AuthService.create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Logout current user (client should discard tokens)
    """
    # In a production system, you might want to:
    # 1. Add the token to a blacklist
    # 2. Clear any server-side sessions
    # 3. Log the logout event
    
    logger.info(f"User {current_user.email} logged out")
    
    # Clear any cookies if used
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user information
    """
    return UserResponse.model_validate(current_user)


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIKeyResponse:
    """
    Create a new API key for the current user
    """
    from ..models import APIKey
    from datetime import datetime, timedelta
    
    # Generate API key
    api_key = AuthService.generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key object
    new_key = APIKey(
        key=api_key,
        name=key_data.name,
        description=key_data.description,
        user_id=current_user.id,
        scopes=key_data.scopes,
        expires_at=expires_at
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    logger.info(f"API key created for user {current_user.email}: {key_data.name}")
    
    return APIKeyResponse.model_validate(new_key)


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[APIKeyResponse]:
    """
    List all API keys for the current user
    """
    from ..models import APIKey
    
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    return [APIKeyResponse.model_validate(key) for key in keys]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Revoke an API key
    """
    from ..models import APIKey
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = False
    db.commit()
    
    logger.info(f"API key {api_key.name} revoked by user {current_user.email}")
    
    return {"message": "API key revoked successfully"}
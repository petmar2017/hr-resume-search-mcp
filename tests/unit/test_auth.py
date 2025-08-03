"""
Unit Tests for Authentication Functions
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from jose import JWTError

# Import authentication functions to test
# Note: These will be created in api/auth.py
from api.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    get_current_user,
    AuthService
)
from api.models import User
from api.config import get_settings


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    def test_password_hashing_and_verification(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = get_password_hash(password)
        
        # Verify it's actually hashed (not plain text)
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 chars
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword123!", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "Password123!"
        password2 = "Password456!"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_salts(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "TestPassword123!"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Should be different due to random salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Decode token without verification to check structure
        settings = get_settings()
        decoded = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == 1
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration"""
        user_data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        settings = get_settings()
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        
        # Check expiration is approximately 15 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 1 minute tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 60
    
    def test_verify_valid_token(self):
        """Test verification of valid token"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(data=user_data)
        
        payload = verify_token(token)
        
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 1
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(JWTError):
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Test verification of expired token"""
        user_data = {"sub": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        with pytest.raises(JWTError):
            verify_token(token)
    
    def test_verify_token_wrong_secret(self):
        """Test verification with wrong secret key"""
        user_data = {"sub": "test@example.com"}
        token = create_access_token(data=user_data)
        
        # Mock wrong secret
        with patch('api.config.get_settings') as mock_settings:
            mock_settings.return_value.JWT_SECRET_KEY = "wrong-secret"
            mock_settings.return_value.JWT_ALGORITHM = "HS256"
            
            with pytest.raises(JWTError):
                verify_token(token)


class TestAuthService:
    """Test AuthService class"""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing"""
        return AuthService()
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.hashed_password = get_password_hash("TestPassword123!")
        user.is_active = True
        user.is_verified = True
        return user
    
    def test_authenticate_user_success(self, auth_service, mock_user):
        """Test successful user authentication"""
        with patch.object(auth_service, 'get_user_by_email', return_value=mock_user):
            result = auth_service.authenticate_user("test@example.com", "TestPassword123!")
            
            assert result == mock_user
    
    def test_authenticate_user_wrong_password(self, auth_service, mock_user):
        """Test authentication with wrong password"""
        with patch.object(auth_service, 'get_user_by_email', return_value=mock_user):
            result = auth_service.authenticate_user("test@example.com", "WrongPassword")
            
            assert result is False
    
    def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user"""
        with patch.object(auth_service, 'get_user_by_email', return_value=None):
            result = auth_service.authenticate_user("nonexistent@example.com", "password")
            
            assert result is False
    
    def test_authenticate_inactive_user(self, auth_service, mock_user):
        """Test authentication with inactive user"""
        mock_user.is_active = False
        
        with patch.object(auth_service, 'get_user_by_email', return_value=mock_user):
            result = auth_service.authenticate_user("test@example.com", "TestPassword123!")
            
            assert result is False
    
    def test_create_user_success(self, auth_service):
        """Test successful user creation"""
        user_data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "NewPassword123!",
            "full_name": "New User"
        }
        
        with patch.object(auth_service, 'create_user_in_db') as mock_create:
            mock_user = Mock(spec=User)
            mock_user.id = 2
            mock_user.email = user_data["email"]
            mock_user.username = user_data["username"]
            mock_create.return_value = mock_user
            
            result = auth_service.create_user(user_data)
            
            assert result == mock_user
            mock_create.assert_called_once()
            
            # Verify password was hashed
            call_args = mock_create.call_args[0][0]
            assert call_args["password"] != user_data["password"]  # Should be hashed
    
    def test_create_user_duplicate_email(self, auth_service):
        """Test user creation with duplicate email"""
        user_data = {
            "email": "existing@example.com",
            "username": "newuser",
            "password": "Password123!"
        }
        
        with patch.object(auth_service, 'get_user_by_email', return_value=Mock()):
            with pytest.raises(ValueError, match="already exists"):
                auth_service.create_user(user_data)
    
    def test_validate_user_permissions(self, auth_service, mock_user):
        """Test user permission validation"""
        # Test active user
        assert auth_service.validate_user_permissions(mock_user) is True
        
        # Test inactive user
        mock_user.is_active = False
        assert auth_service.validate_user_permissions(mock_user) is False
        
        # Test unverified user (should still be allowed for basic access)
        mock_user.is_active = True
        mock_user.is_verified = False
        assert auth_service.validate_user_permissions(mock_user) is True


class TestGetCurrentUser:
    """Test get_current_user dependency"""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user):
        """Test successful current user retrieval"""
        token = create_access_token(data={"sub": "test@example.com", "user_id": 1})
        
        with patch('api.auth.get_user_by_id', return_value=mock_user):
            user = await get_current_user(token)
            
            assert user == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid.token")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test current user retrieval when user doesn't exist"""
        from fastapi import HTTPException
        
        token = create_access_token(data={"sub": "test@example.com", "user_id": 999})
        
        with patch('api.auth.get_user_by_id', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, mock_user):
        """Test current user retrieval with inactive user"""
        from fastapi import HTTPException
        
        mock_user.is_active = False
        token = create_access_token(data={"sub": "test@example.com", "user_id": 1})
        
        with patch('api.auth.get_user_by_id', return_value=mock_user):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            
            assert exc_info.value.status_code == 401


class TestPasswordValidation:
    """Test password validation functions"""
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        from api.auth import validate_password_strength
        
        # Valid passwords
        assert validate_password_strength("StrongPassword123!") is True
        assert validate_password_strength("Another$ecure1") is True
        
        # Invalid passwords
        assert validate_password_strength("weak") is False  # Too short
        assert validate_password_strength("nouppercasehere123!") is False  # No uppercase
        assert validate_password_strength("NOLOWERCASEHERE123!") is False  # No lowercase
        assert validate_password_strength("NoNumbers!") is False  # No numbers
        assert validate_password_strength("NoSpecialChars123") is False  # No special chars
    
    def test_email_validation(self):
        """Test email validation"""
        from api.auth import validate_email_format
        
        # Valid emails
        assert validate_email_format("test@example.com") is True
        assert validate_email_format("user.name+tag@domain.co.uk") is True
        
        # Invalid emails
        assert validate_email_format("invalid-email") is False
        assert validate_email_format("@domain.com") is False
        assert validate_email_format("user@") is False
        assert validate_email_format("user space@domain.com") is False


class TestRateLimitingHelpers:
    """Test rate limiting helper functions"""
    
    def test_generate_rate_limit_key(self):
        """Test rate limit key generation"""
        from api.auth import generate_rate_limit_key
        
        key1 = generate_rate_limit_key("user@example.com", "/api/v1/resumes")
        key2 = generate_rate_limit_key("user@example.com", "/api/v1/search")
        key3 = generate_rate_limit_key("other@example.com", "/api/v1/resumes")
        
        # Keys should be different for different users/endpoints
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
        
        # Same user/endpoint should generate same key
        key1_repeat = generate_rate_limit_key("user@example.com", "/api/v1/resumes")
        assert key1 == key1_repeat
    
    def test_check_rate_limit(self):
        """Test rate limit checking"""
        from api.auth import check_rate_limit
        
        with patch('api.auth.redis_client') as mock_redis:
            # Mock Redis responses
            mock_redis.get.return_value = None  # No existing limit
            mock_redis.setex.return_value = True
            
            # First request should be allowed
            result = check_rate_limit("test_key", limit=10, window=60)
            assert result is True
            
            # Mock existing count below limit
            mock_redis.get.return_value = "5"
            mock_redis.incr.return_value = 6
            
            result = check_rate_limit("test_key", limit=10, window=60)
            assert result is True
            
            # Mock existing count at limit
            mock_redis.get.return_value = "10"
            
            result = check_rate_limit("test_key", limit=10, window=60)
            assert result is False
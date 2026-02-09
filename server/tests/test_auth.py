"""
Tests for JWT Authentication Module.

Tests cover:
1. JWT token creation and verification
2. Token expiry and refresh
3. Authentication endpoints (login, refresh, validate)
4. Authorization dependencies
5. Security edge cases (invalid tokens, wrong user type, etc.)

Run with: pytest tests/test_auth.py -v
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import jwt

from app.shared.auth.jwt import (
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_employer_access_token,
    create_employer_refresh_token,
    create_candidate_access_token,
    create_candidate_refresh_token,
    verify_token,
    verify_employer_token,
    verify_candidate_token,
    TokenVerificationError,
    EmployerTokenPayload,
    CandidateTokenPayload,
)
from app.config.settings import settings


# =============================================================================
# TEST DATA
# =============================================================================

TEST_EMPLOYER_ID = uuid4()
TEST_EMPLOYER_EMAIL = "testemployer@example.com"
TEST_CANDIDATE_ID = uuid4()
TEST_CANDIDATE_MOBILE = "9876543210"


# =============================================================================
# TOKEN CREATION TESTS
# =============================================================================

class TestEmployerTokenCreation:
    """Tests for employer token creation."""
    
    def test_create_employer_access_token_returns_string(self):
        """Access token should be a non-empty string."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_employer_access_token_contains_correct_payload(self):
        """Access token should contain employer_id, email, and correct type."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        # Decode without verification to check payload
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        assert payload["employer_id"] == str(TEST_EMPLOYER_ID)
        assert payload["email"] == TEST_EMPLOYER_EMAIL
        assert payload["token_type"] == "access"
        assert payload["user_type"] == "employer"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_employer_access_token_has_correct_expiry(self):
        """Access token should have correct expiry time."""
        before = datetime.now(timezone.utc)
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        after = datetime.now(timezone.utc)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Expiry should be approximately ACCESS_TOKEN_EXPIRE_MINUTES from now
        expected_exp_min = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES - 1)
        expected_exp_max = after + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES + 1)
        
        assert expected_exp_min <= exp <= expected_exp_max
    
    def test_create_employer_access_token_custom_expiry(self):
        """Access token should respect custom expiry delta."""
        custom_delta = timedelta(hours=1)
        before = datetime.now(timezone.utc)
        
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
            expires_delta=custom_delta,
        )
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Should expire in ~1 hour
        expected = before + custom_delta
        assert abs((exp - expected).total_seconds()) < 5  # Allow 5 second tolerance
    
    def test_create_employer_refresh_token_contains_correct_payload(self):
        """Refresh token should have token_type='refresh'."""
        token = create_employer_refresh_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        assert payload["employer_id"] == str(TEST_EMPLOYER_ID)
        assert payload["token_type"] == "refresh"
        assert payload["user_type"] == "employer"


class TestCandidateTokenCreation:
    """Tests for candidate token creation."""
    
    def test_create_candidate_access_token_returns_string(self):
        """Access token should be a non-empty string."""
        token = create_candidate_access_token(
            candidate_id=TEST_CANDIDATE_ID,
            mobile_number=TEST_CANDIDATE_MOBILE,
        )
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_candidate_access_token_contains_correct_payload(self):
        """Access token should contain candidate_id, mobile_number, and correct type."""
        token = create_candidate_access_token(
            candidate_id=TEST_CANDIDATE_ID,
            mobile_number=TEST_CANDIDATE_MOBILE,
        )
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        assert payload["candidate_id"] == str(TEST_CANDIDATE_ID)
        assert payload["mobile_number"] == TEST_CANDIDATE_MOBILE
        assert payload["token_type"] == "access"
        assert payload["user_type"] == "candidate"
    
    def test_create_candidate_refresh_token_contains_correct_payload(self):
        """Refresh token should have token_type='refresh'."""
        token = create_candidate_refresh_token(
            candidate_id=TEST_CANDIDATE_ID,
            mobile_number=TEST_CANDIDATE_MOBILE,
        )
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        
        assert payload["candidate_id"] == str(TEST_CANDIDATE_ID)
        assert payload["token_type"] == "refresh"
        assert payload["user_type"] == "candidate"


# =============================================================================
# TOKEN VERIFICATION TESTS
# =============================================================================

class TestTokenVerification:
    """Tests for generic token verification."""
    
    def test_verify_valid_token_returns_payload(self):
        """Valid token should return decoded payload."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        payload = verify_token(token)
        
        assert payload["employer_id"] == str(TEST_EMPLOYER_ID)
        assert payload["email"] == TEST_EMPLOYER_EMAIL
    
    def test_verify_expired_token_raises_error(self):
        """Expired token should raise TokenVerificationError."""
        # Create token with past expiry
        payload = {
            "sub": str(TEST_EMPLOYER_ID),
            "employer_id": str(TEST_EMPLOYER_ID),
            "email": TEST_EMPLOYER_EMAIL,
            "token_type": "access",
            "user_type": "employer",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
        
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_token(expired_token)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_verify_invalid_signature_raises_error(self):
        """Token with invalid signature should raise TokenVerificationError."""
        # Create token with wrong secret
        payload = {
            "sub": str(TEST_EMPLOYER_ID),
            "employer_id": str(TEST_EMPLOYER_ID),
            "email": TEST_EMPLOYER_EMAIL,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        invalid_token = jwt.encode(payload, "wrong-secret-key", algorithm=ALGORITHM)
        
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_token(invalid_token)
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_verify_malformed_token_raises_error(self):
        """Malformed token should raise TokenVerificationError."""
        with pytest.raises(TokenVerificationError):
            verify_token("not.a.valid.jwt.token")
    
    def test_verify_empty_token_raises_error(self):
        """Empty token should raise TokenVerificationError."""
        with pytest.raises(TokenVerificationError):
            verify_token("")


class TestEmployerTokenVerification:
    """Tests for employer-specific token verification."""
    
    def test_verify_employer_token_returns_payload_object(self):
        """Valid employer token should return EmployerTokenPayload."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        payload = verify_employer_token(token)
        
        assert isinstance(payload, EmployerTokenPayload)
        assert payload.employer_id == TEST_EMPLOYER_ID
        assert payload.email == TEST_EMPLOYER_EMAIL
        assert payload.token_type == "access"
    
    def test_verify_employer_token_rejects_candidate_token(self):
        """Candidate token should be rejected by verify_employer_token."""
        token = create_candidate_access_token(
            candidate_id=TEST_CANDIDATE_ID,
            mobile_number=TEST_CANDIDATE_MOBILE,
        )
        
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_employer_token(token)
        
        assert "not an employer token" in str(exc_info.value).lower()


class TestCandidateTokenVerification:
    """Tests for candidate-specific token verification."""
    
    def test_verify_candidate_token_returns_payload_object(self):
        """Valid candidate token should return CandidateTokenPayload."""
        token = create_candidate_access_token(
            candidate_id=TEST_CANDIDATE_ID,
            mobile_number=TEST_CANDIDATE_MOBILE,
        )
        
        payload = verify_candidate_token(token)
        
        assert isinstance(payload, CandidateTokenPayload)
        assert payload.candidate_id == TEST_CANDIDATE_ID
        assert payload.mobile_number == TEST_CANDIDATE_MOBILE
        assert payload.token_type == "access"
    
    def test_verify_candidate_token_rejects_employer_token(self):
        """Employer token should be rejected by verify_candidate_token."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        with pytest.raises(TokenVerificationError) as exc_info:
            verify_candidate_token(token)
        
        assert "not a candidate token" in str(exc_info.value).lower()


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestEmployerLoginEndpoint:
    """Tests for employer login endpoint."""
    
    def test_employer_login_success(self, test_client, sample_employer_data):
        """Valid employer should get tokens on login."""
        # First create an employer
        create_response = test_client.post(
            "/api/v1/employers",
            json=sample_employer_data,
        )
        assert create_response.status_code == 201
        created_email = sample_employer_data["email"]
        
        # Now login
        login_response = test_client.post(
            "/api/v1/auth/employer/login",
            json={"email": created_email},
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == created_email
        assert "employer_id" in data
        assert data["expires_in"] > 0
    
    def test_employer_login_invalid_email(self, test_client):
        """Invalid email should return 401."""
        response = test_client.post(
            "/api/v1/auth/employer/login",
            json={"email": "nonexistent@example.com"},
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_employer_login_missing_email(self, test_client):
        """Missing email should return 422."""
        response = test_client.post(
            "/api/v1/auth/employer/login",
            json={},
        )
        
        assert response.status_code == 422


class TestCandidateLoginEndpoint:
    """Tests for candidate login endpoint."""
    
    def test_candidate_login_success(self, test_client):
        """Valid candidate should get tokens on login."""
        import random
        
        # Generate a valid 10-digit Indian mobile number (starts with 7,8,9)
        mobile = f"9{random.randint(100000000, 999999999)}"
        
        # First create a candidate using the signup endpoint
        create_response = test_client.post(
            "/api/v1/candidates/signup",
            json={
                "mobile": mobile,
                "name": "Test Candidate",
                "current_location": "Mumbai, Maharashtra",
                "preferred_location": "Pune, Maharashtra",
            },
        )
        assert create_response.status_code == 201, create_response.text
        
        # Now login
        login_response = test_client.post(
            "/api/v1/auth/candidate/login",
            json={"mobile_number": mobile},
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["mobile_number"] == mobile
        assert "candidate_id" in data
    
    def test_candidate_login_invalid_mobile(self, test_client):
        """Invalid mobile should return 401."""
        response = test_client.post(
            "/api/v1/auth/candidate/login",
            json={"mobile_number": "0000000000"},
        )
        
        assert response.status_code == 401


class TestTokenRefreshEndpoint:
    """Tests for token refresh endpoint."""
    
    def test_refresh_token_returns_new_access_token(self, test_client, sample_employer_data):
        """Valid refresh token should return new access token."""
        # Create employer and login
        test_client.post("/api/v1/employers", json=sample_employer_data)
        login_response = test_client.post(
            "/api/v1/auth/employer/login",
            json={"email": sample_employer_data["email"]},
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token
        refresh_response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    def test_refresh_token_rejects_access_token(self, test_client, sample_employer_data):
        """Using access token as refresh should fail."""
        # Create employer and login
        test_client.post("/api/v1/employers", json=sample_employer_data)
        login_response = test_client.post(
            "/api/v1/auth/employer/login",
            json={"email": sample_employer_data["email"]},
        )
        access_token = login_response.json()["access_token"]
        
        # Try to use access token as refresh token
        refresh_response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        assert refresh_response.status_code == 401
        assert "refresh" in refresh_response.json()["detail"].lower()
    
    def test_refresh_token_rejects_invalid_token(self, test_client):
        """Invalid refresh token should fail."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        
        assert response.status_code == 401


class TestTokenValidationEndpoint:
    """Tests for token validation endpoint."""
    
    def test_validate_valid_token(self, test_client, sample_employer_data):
        """Valid token should return valid=true with user info."""
        # Create employer and login
        test_client.post("/api/v1/employers", json=sample_employer_data)
        login_response = test_client.post(
            "/api/v1/auth/employer/login",
            json={"email": sample_employer_data["email"]},
        )
        access_token = login_response.json()["access_token"]
        
        # Validate token
        validate_response = test_client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert validate_response.status_code == 200
        data = validate_response.json()
        
        assert data["valid"] is True
        assert data["user_type"] == "employer"
        assert data["email"] == sample_employer_data["email"]
        assert data["expires_at"] is not None
    
    def test_validate_invalid_token(self, test_client):
        """Invalid token should return valid=false."""
        response = test_client.get(
            "/api/v1/auth/validate",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is False
    
    def test_validate_missing_token(self, test_client):
        """Missing token should return valid=false."""
        response = test_client.get("/api/v1/auth/validate")
        
        assert response.status_code == 200
        assert response.json()["valid"] is False


# =============================================================================
# SECURITY EDGE CASE TESTS
# =============================================================================

class TestSecurityEdgeCases:
    """Tests for security edge cases and attack prevention."""
    
    def test_token_cannot_be_modified(self):
        """Modifying token payload should invalidate signature."""
        token = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        # Tamper with the payload (change email)
        parts = token.split(".")
        import base64
        import json
        
        # Decode payload (with padding fix)
        payload_b64 = parts[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)  # Add padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Modify email
        payload["email"] = "hacker@evil.com"
        
        # Re-encode payload
        modified_payload = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        
        # Reconstruct token with modified payload
        tampered_token = f"{parts[0]}.{modified_payload}.{parts[2]}"
        
        # Should fail verification
        with pytest.raises(TokenVerificationError):
            verify_token(tampered_token)
    
    def test_token_with_future_iat_still_works(self):
        """Token with future iat (clock skew) should still work since iat check is disabled."""
        payload = {
            "sub": str(TEST_EMPLOYER_ID),
            "employer_id": str(TEST_EMPLOYER_ID),
            "email": TEST_EMPLOYER_EMAIL,
            "token_type": "access",
            "user_type": "employer",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc) + timedelta(seconds=30),  # Slight future
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
        
        # Should verify since we disabled iat check to handle clock skew
        result = verify_token(token)
        assert result["employer_id"] == str(TEST_EMPLOYER_ID)
    
    def test_different_users_get_different_tokens(self):
        """Different users should get different tokens."""
        id1 = uuid4()
        id2 = uuid4()
        
        token1 = create_employer_access_token(employer_id=id1, email="user1@test.com")
        token2 = create_employer_access_token(employer_id=id2, email="user2@test.com")
        
        assert token1 != token2
        
        payload1 = verify_token(token1)
        payload2 = verify_token(token2)
        
        assert payload1["employer_id"] != payload2["employer_id"]
    
    def test_refresh_token_has_longer_expiry_than_access_token(self):
        """Refresh token should expire later than access token."""
        access = create_employer_access_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        refresh = create_employer_refresh_token(
            employer_id=TEST_EMPLOYER_ID,
            email=TEST_EMPLOYER_EMAIL,
        )
        
        access_payload = jwt.decode(access, settings.secret_key, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(refresh, settings.secret_key, algorithms=[ALGORITHM])
        
        assert refresh_payload["exp"] > access_payload["exp"]


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

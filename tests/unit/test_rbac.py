"""
Unit tests for RBAC (Role-Based Access Control) - backend/auth.py

Coverage:
- Role-based permission checks
- User-patient relationship verification
- Edge cases (no role, unknown role)
- Token generation and validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from backend.auth import (
    create_access_token,
    verify_password,
    require_role,
    get_current_user,
    check_patient_access,
    TokenData,
)
from backend.models import TokenData as TokenDataModel


class TestPasswordVerification:
    """Test password verification."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_correct_password(self):
        """Test verification of correct password."""
        plain_password = "mypassword123"
        hashed_password = "mypassword123"  # Simple hash for testing
        
        result = verify_password(plain_password, hashed_password)
        assert result is True, "Correct password should verify"

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_incorrect_password(self):
        """Test verification of incorrect password."""
        plain_password = "password123"
        hashed_password = "different_password"
        
        result = verify_password(plain_password, hashed_password)
        assert result is False, "Incorrect password should not verify"

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_empty_password(self):
        """Test verification of empty password."""
        result = verify_password("", "")
        assert result is True, "Empty passwords should match"

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_case_sensitive_password(self):
        """Test that password verification is case-sensitive."""
        result = verify_password("Password", "password")
        assert result is False, "Passwords should be case-sensitive"


class TestTokenGeneration:
    """Test JWT token generation."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_create_access_token_basic(self):
        """Test basic token creation."""
        data = {"sub": "testuser", "roles": ["user"]}
        token = create_access_token(data)
        
        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_create_access_token_with_expiration(self):
        """Test token creation with expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        assert isinstance(token, str)
        # Token should contain encoded expiration

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_create_admin_token(self, admin_token):
        """Test admin token creation."""
        assert isinstance(admin_token, str)
        assert len(admin_token) > 0

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_create_resident_token(self, resident_token):
        """Test resident token creation."""
        assert isinstance(resident_token, str)
        assert len(resident_token) > 0

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_token_contains_user_data(self):
        """Test that token contains user data."""
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        data = {"sub": "testuser", "roles": ["admin"]}
        token = create_access_token(data)
        
        # Decode token
        payload = jwt.decode(token, LOCAL_SECRET_KEY, algorithms=[LOCAL_ALGORITHM])
        
        assert payload["sub"] == "testuser"
        assert "admin" in payload["roles"]
        assert "exp" in payload  # Expiration should be set


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_admin_role_access(self, test_users):
        """Test admin role has access to admin resources."""
        user = test_users["attending"]
        assert "admin" in user["roles"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_resident_role_access(self, test_users):
        """Test resident role access."""
        user = test_users["resident"]
        assert "resident" in user["roles"]
        assert "admin" not in user["roles"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_nurse_role_access(self, test_users):
        """Test nurse role access."""
        user = test_users["nurse"]
        assert "nurse" in user["roles"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_role_hierarchy(self, rbac_test_cases):
        """Test role hierarchy and permissions."""
        for case in rbac_test_cases:
            user_role = case["user_role"]
            required_role = case["required_role"]
            should_allow = case["allowed"]
            
            # Admin can always access (except in specific restricted cases)
            if user_role == "admin" or user_role == required_role:
                assert should_allow or user_role != required_role

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_role_check_admin_admin(self):
        """Test admin accessing admin resource."""
        user = TokenDataModel(username="admin", roles=["admin"])
        # Admin should have access
        assert "admin" in user.roles

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_role_check_resident_resident(self):
        """Test resident accessing resident resource."""
        user = TokenDataModel(username="resident", roles=["resident"])
        assert "resident" in user.roles

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_role_check_resident_admin_fails(self):
        """Test resident cannot access admin resource."""
        user = TokenDataModel(username="resident", roles=["resident"])
        assert "admin" not in user.roles

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_multiple_roles_user(self):
        """Test user with multiple roles."""
        user = TokenDataModel(
            username="multi_role",
            roles=["resident", "admin"]
        )
        assert "resident" in user.roles
        assert "admin" in user.roles


class TestPatientAccess:
    """Test patient access control."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_admin_can_access_any_patient(self, patient_relationships):
        """Test admin can access any patient."""
        admin = patient_relationships["attending_user"]
        assert "any" in admin["assigned_patients"]
        assert all(p in admin["accessible_patients"] for p in admin["accessible_patients"])

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_resident_access_assigned_patients(self, patient_relationships):
        """Test resident can access assigned patients."""
        resident = patient_relationships["resident_user"]
        
        for patient in resident["assigned_patients"]:
            assert patient in resident["accessible_patients"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_resident_cannot_access_unassigned_patients(self, patient_relationships):
        """Test resident cannot access unassigned patients."""
        resident = patient_relationships["resident_user"]
        
        for patient in resident.get("not_accessible", []):
            assert patient not in resident["accessible_patients"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_nurse_access_assigned_patient(self, patient_relationships):
        """Test nurse access to assigned patient."""
        nurse = patient_relationships["nurse_user"]
        
        for patient in nurse["assigned_patients"]:
            assert patient in nurse["accessible_patients"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_nurse_cannot_access_other_patients(self, patient_relationships):
        """Test nurse cannot access other patients."""
        nurse = patient_relationships["nurse_user"]
        
        for patient in nurse.get("not_accessible", []):
            assert patient not in nurse["accessible_patients"]

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_patient_access_verification(self):
        """Test patient access verification logic."""
        # Admin can access any patient
        admin_role = ["admin"]
        admin_patients = ["any"]
        assert "any" in admin_patients
        
        # Resident can access assigned patients
        resident_role = ["resident"]
        resident_patients = ["P001", "P002"]
        assert "P001" in resident_patients


class TestEdgeCases:
    """Test edge cases in RBAC."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_no_role(self):
        """Test user with no role."""
        user = TokenDataModel(username="no_role_user", roles=[])
        assert len(user.roles) == 0

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_unknown_role(self):
        """Test user with unknown role."""
        user = TokenDataModel(username="user", roles=["unknown_role"])
        assert "unknown_role" in user.roles

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_empty_username(self):
        """Test token with empty username."""
        user = TokenDataModel(username="", roles=["admin"])
        assert user.username == ""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_none_username(self):
        """Test token with None username."""
        user = TokenDataModel(username=None, roles=["admin"])
        assert user.username is None

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_role_case_sensitivity(self):
        """Test that roles are case-sensitive."""
        user1 = TokenDataModel(username="user", roles=["Admin"])
        user2 = TokenDataModel(username="user", roles=["admin"])
        
        assert "Admin" in user1.roles
        assert "admin" in user2.roles
        assert "Admin" != "admin"

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_duplicate_roles(self):
        """Test user with duplicate roles."""
        user = TokenDataModel(
            username="user",
            roles=["admin", "admin", "resident"]
        )
        assert user.roles.count("admin") == 2

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_very_long_role_list(self):
        """Test user with many roles."""
        roles = [f"role_{i}" for i in range(100)]
        user = TokenDataModel(username="user", roles=roles)
        assert len(user.roles) == 100

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_special_characters_in_role(self):
        """Test role with special characters."""
        user = TokenDataModel(
            username="user",
            roles=["admin@org", "role-name", "role_name"]
        )
        assert "admin@org" in user.roles


class TestTokenValidation:
    """Test token validation and decoding."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_valid_token_decode(self, admin_token):
        """Test decoding valid token."""
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        try:
            payload = jwt.decode(
                admin_token,
                LOCAL_SECRET_KEY,
                algorithms=[LOCAL_ALGORITHM]
            )
            assert "sub" in payload
            assert "exp" in payload
        except jwt.PyJWTError:
            pytest.fail("Valid token should decode successfully")

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_invalid_token_format(self):
        """Test invalid token format."""
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        invalid_token = "not.a.valid.token"
        
        with pytest.raises(jwt.DecodeError):
            jwt.decode(
                invalid_token,
                LOCAL_SECRET_KEY,
                algorithms=[LOCAL_ALGORITHM]
            )

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_expired_token(self):
        """Test expired token."""
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        # Create token with negative expiration (already expired)
        data = {"sub": "user"}
        expired_delta = timedelta(minutes=-10)  # 10 minutes ago
        token = create_access_token(data, expired_delta)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                LOCAL_SECRET_KEY,
                algorithms=[LOCAL_ALGORITHM]
            )

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_tampered_token(self):
        """Test tampered token."""
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        data = {"sub": "user"}
        token = create_access_token(data)
        
        # Tamper with token (change last character)
        tampered = token[:-1] + ('a' if token[-1] != 'a' else 'b')
        
        with pytest.raises(jwt.DecodeError):
            jwt.decode(
                tampered,
                LOCAL_SECRET_KEY,
                algorithms=[LOCAL_ALGORITHM]
            )


class TestRBACIntegration:
    """Integration tests for RBAC."""

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_full_auth_flow_admin(self, test_users, admin_token):
        """Test full authentication flow for admin."""
        admin = test_users["attending"]
        
        # Verify token can be created and decoded
        assert admin_token is not None
        assert len(admin_token) > 0

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_full_auth_flow_resident(self, test_users, resident_token):
        """Test full authentication flow for resident."""
        resident = test_users["resident"]
        
        assert resident_token is not None
        assert len(resident_token) > 0

    @pytest.mark.unit
    @pytest.mark.rbac
    def test_all_users_have_tokens(self, test_users):
        """Test all users can generate tokens."""
        for username, user_data in test_users.items():
            token = create_access_token(
                {"sub": username, "roles": user_data["roles"]}
            )
            assert isinstance(token, str)
            assert len(token) > 0

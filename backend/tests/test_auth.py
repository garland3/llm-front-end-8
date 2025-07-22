import pytest
from app.auth.authorization import is_user_in_group

class TestAuthorization:
    def test_is_user_in_group_valid_user_valid_group(self):
        assert is_user_in_group("test@test.com", "default") == True
        assert is_user_in_group("test@test.com", "admin") == True
        assert is_user_in_group("test@test.com", "mcp_users") == True

    def test_is_user_in_group_valid_user_invalid_group(self):
        assert is_user_in_group("test@test.com", "nonexistent") == False

    def test_is_user_in_group_invalid_user(self):
        assert is_user_in_group("nonexistent@test.com", "default") == True
        assert is_user_in_group("nonexistent@test.com", "admin") == False

    def test_is_user_in_group_admin_user(self):
        assert is_user_in_group("admin@example.com", "super_admin") == True
        assert is_user_in_group("admin@example.com", "admin") == True
        assert is_user_in_group("admin@example.com", "default") == True

    def test_is_user_in_group_regular_user(self):
        assert is_user_in_group("user@example.com", "default") == True
        assert is_user_in_group("user@example.com", "mcp_users") == True
        assert is_user_in_group("user@example.com", "admin") == False
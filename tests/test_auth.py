"""
Test authentication endpoints
"""

import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication functionality"""

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        response = await client.post("/api/auth/token", data={
            "username": "invalid",
            "password": "invalid"
        })
        assert response.status_code == 401

    async def test_login_valid_credentials(self, authenticated_client: AsyncClient):
        """Test login with valid credentials"""
        # The authenticated_client fixture already handles login
        # Test that we can access protected endpoint
        response = await authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["username"] == "testuser"
        assert user_data["is_admin"] == True

    async def test_register_user(self, client: AsyncClient):
        """Test user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "newpassword",
            "is_admin": False
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user["username"] == "newuser"
        assert created_user["is_admin"] == False

    async def test_register_duplicate_username(self, authenticated_client: AsyncClient):
        """Test registration with duplicate username"""
        user_data = {
            "username": "testuser",  # This already exists
            "email": "another@example.com",
            "password": "password",
            "is_admin": False
        }
        
        response = await authenticated_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_list_users_admin_only(self, authenticated_client: AsyncClient):
        """Test listing users requires admin privileges"""
        response = await authenticated_client.get("/api/auth/users")
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) >= 1  # At least the test user

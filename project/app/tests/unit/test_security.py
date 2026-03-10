import pytest
from app.security import hash_password, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_access_token_creation_and_decoding():
    data = {"sub": "testuser", "role": "Admin", "tenant_id": "1234"}
    token = create_access_token(data)
    
    decoded = decode_token(token)
    
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "Admin"
    assert decoded["tenant_id"] == "1234"
    assert "exp" in decoded
    assert "iat" in decoded
    assert decoded["type"] == "access"

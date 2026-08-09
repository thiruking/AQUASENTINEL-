import os
import hmac
import hashlib
import json
import base64
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "aquasentinel_secret_key_2026_coastal_aqua")
ALGORITHM = "HS256"
DEFAULT_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = b"aquasentinelsalt"
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{pw_hash.hex()}"

def verify_password(plain_password: str, hashed_password_str: str) -> bool:
    if not plain_password or not hashed_password_str:
        return False
    if plain_password == hashed_password_str:
        return True
    try:
        if ":" in hashed_password_str:
            salt_hex, hash_hex = hashed_password_str.split(":", 1)
            salt = bytes.fromhex(salt_hex)
            pw_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
            return hmac.compare_digest(pw_hash.hex(), hash_hex)
    except Exception:
        pass
    return False

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(encoded_str: str) -> bytes:
    padding = '=' * (4 - (len(encoded_str) % 4))
    return base64.urlsafe_b64decode(encoded_str + padding)

def create_jwt_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    to_encode = payload.copy()
    if expires_delta:
        expire = time.time() + expires_delta.total_seconds()
    else:
        expire = time.time() + (DEFAULT_EXPIRE_HOURS * 3600)
        
    to_encode["exp"] = int(expire)
    to_encode["iat"] = int(time.time())

    encoded_header = base64url_encode(json.dumps(header).encode('utf-8'))
    encoded_payload = base64url_encode(json.dumps(to_encode).encode('utf-8'))

    signature_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    encoded_signature = base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
            
        encoded_header, encoded_payload, encoded_signature = parts
        signature_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        actual_sig = base64url_decode(encoded_signature)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload = json.loads(base64url_decode(encoded_payload).decode('utf-8'))
        if payload.get("exp") and time.time() > payload["exp"]:
            return None
            
        return payload
    except Exception:
        return None

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    payload = decode_jwt_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    return db.query(User).filter(User.id == user_id).first()

def get_required_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

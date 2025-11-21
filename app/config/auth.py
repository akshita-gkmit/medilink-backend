from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config.config import Config
import logging

logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

bearer_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def create_access_token(data: dict) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            Config.SECRET_KEY,
            algorithm=Config.ALGORITHM
        )
    except Exception as e:
        logger.error(f"Access token creation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")


def create_refresh_token(data: dict) -> str:
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})

        return jwt.encode(
            to_encode,
            Config.REFRESH_SECRET_KEY,
            algorithm=Config.ALGORITHM
        )
    except Exception as e:
        logger.error(f"Refresh token creation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, 
            Config.SECRET_KEY, 
            algorithms=[Config.ALGORITHM]
        )
        return payload

    except JWTError as e:
        logger.warning(f"Access token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            Config.SECRET_KEY,
            algorithms=[Config.ALGORITHM]
        )

        return {
            "id": payload.get("id"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }

    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    except Exception as e:
        logger.error(f"Unexpected token parsing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token,
            Config.REFRESH_SECRET_KEY,
            algorithms=[Config.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return payload

    except JWTError as e:
        logger.warning(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    except Exception as e:
        logger.error(f"Unexpected refresh token error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class RoleChecker:

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=[Config.ALGORITHM]
            )

            role = payload.get("role")
            exp = payload.get("exp")

            if not role:
                raise HTTPException(status_code=401, detail="Role missing in token")

            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(status_code=401, detail="Token expired")

            if role not in self.allowed_roles:
                raise HTTPException(status_code=403, detail="Forbidden")

        except HTTPException:
            raise

        except JWTError as e:
            logger.warning(f"Role check failed (token error): {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        except Exception as e:
            logger.error(f"Unexpected role check error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

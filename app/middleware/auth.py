import datetime
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

security = HTTPBearer()

class User(BaseModel):
    username: str
    is_admin: bool = False
    
def hash_password(password: str) ->str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(username: str,
                        expirese_delta_Seconds: int | None = None,
                        is_admin: bool = False) -> str:
    if expirese_delta_Seconds is None:
        expirese_delta_Seconds = settings.jwt_expiration_minutes * 60
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=expirese_delta_Seconds
    )
    payload = {
        "sub": username,
        "is_admin": is_admin,
        "exp": expire
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        username = payload.get("sub")
        if not isinstance(username, str) or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        is_admin: bool = payload.get("is_admin", False)
        return User(username=username, is_admin=is_admin)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
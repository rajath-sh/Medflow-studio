from fastapi import Depends, HTTPException, status
from app.security import get_current_user


def require_roles(*roles: str):
    def checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )
        return user

    return checker

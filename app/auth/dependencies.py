from fastapi import Depends, HTTPException, Request
from sqlmodel import SQLModel, Session, create_engine 
from models.user import User
from services.crud.user import get_user_by_email
from database.database import get_session
from typing import Callable

async def get_current_user(
    request: Request,
    session: Session = Depends(get_session)
) -> User:
    """
    Получает текущего пользователя из токена в заголовке или куке.
    
    Args:
        request (Request): Объект запроса
        session (Session): Сессия базы данных
    
    Returns:
        User: Объект пользователя
    
    Raises:
        HTTPException: Если пользователь не авторизован или не найден
    """
    token = request.cookies.get("access_token")
    
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[len("Bearer "):]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from auth.jwt_handler import verify_access_token
        payload = verify_access_token(token)
        email = payload.get("user")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        user = get_user_by_email(email, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
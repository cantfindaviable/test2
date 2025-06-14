from fastapi import Request
from auth.authenticate import authenticate_cookie
from typing import Optional

async def get_user_id_from_token(request: Request) -> Optional[int]:
    """
    Получает user_id из JWT-токена в куках.
    Если пользователь не авторизован — возвращает None.
    """
    try:
        # передаём куку
        token = request.cookies.get("access_token") 
        if not token:
            return None

        payload = await authenticate_cookie(token)
        return payload.get("id")
    except Exception:
        return None

class AuthMiddleware:
    """
    Middleware для автоматического определения user_id из куки.
    Доступен через request.state.user_id
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)

        user_id = await get_user_id_from_token(request)

        scope["state"]["user_id"] = user_id

        await self.app(scope, receive, send)
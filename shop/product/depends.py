from django.core.handlers.wsgi import WSGIRequest
from jwt import PyJWTError, decode
from datetime import datetime, timezone
from .autf import SECRET_KEY, ALGORITHM
from .models import User


def find_user_by_id(user_id: int = -1) -> User | None:
    if user_id < 0:
        return None
    user = User.objects.get(id=user_id)
    print(type(user))
    return user


def get_token(request: WSGIRequest):
    token = request.COOKIES.get('users_access_token')
    if not token:
        return None
    return token


def get_current_user(request: WSGIRequest):
    token = get_token(request)
    if token is None:
        return None
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        return None

    user_id = payload.get('sub')
    if not user_id:
        return None

    user = find_user_by_id(user_id=int(user_id))
    user = user
    if not user:
        return None
    return user

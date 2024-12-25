from django.core.handlers.wsgi import WSGIRequest
from jwt import PyJWTError, decode
from datetime import datetime, timezone
from .autf import SECRET_KEY, ALGORITHM
from .models import User


def find_user_by_id(user_id: int = -1) -> User | None:
    """
    Поиск пользователя по идентификационному номеру.
    :param user_id: Идентификационный номер пользователя.
    :return: Объект user если пользователь в базе данных найден, None - в противном случае
    """
    if isinstance(user_id, str):
        user_id=int(user_id)
    if user_id < 0:
        return None
    user = User.objects.get(id=user_id)
    return user


def get_token(request: WSGIRequest):
    """
    Получение значения токена из запроса
    :param request: Запрос
    :return: Токен если он имеется и None в противном случае.
    """
    token = request.COOKIES.get('users_access_token')
    if not token:
        return None
    return token


def get_current_user(request: WSGIRequest):
    """
    Получение пользователя по токену.
    :param request: Запрос
    :return: Пользователь - в случае наличия токена и наличия идентификатора пользователя в базе данных, или
             None - в противном случае.
    """
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

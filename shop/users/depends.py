from django.core.handlers.wsgi import WSGIRequest
from jwt import PyJWTError, decode
from datetime import datetime, timezone
from .autf import SECRET_KEY, ALGORITHM, verify_password
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


def check_user(name: str, password: str):
    """
    Проверка данных введённых пользователем на соответствие введённым в базу данных.
    :param name: Имя пользователя
    :param password: Пароль
    :return: Описание статуса операции, статус операции и объект user или None.
        Статус 'Ok' - пользователь прошёл проверку, введённые пользователем данные соответствуют базе данных.
        Описание - Авторизованы.
        Статус 'error' - пользователь не прошёл проверку, либо пользователя с таким именем не существует,
        либо пароль неверный. В описании указанно причина провала проверки
    """
    if name == '':
        return 'Имя пользователя не может быть пустым!', 'error', None
    user = User.objects.filter(username=name).first()
    if user is None:
        return 'Пользователь не найден.', 'error', user
    elif not verify_password(plain_password=password, hashed_password=user.password):
        return 'Пароль не верен!', 'error', user
    elif not user.is_active:
        return 'Пользователь удалён из системы. Для восстановления обратитесь к администратору.', 'error', user
    return 'Авторизованы', 'Ok', user


def check_uniq(users: list, username, email):
    """
    Проверка имени пользователя и адреса электронной почты на уникальность.
    :param users: Список всех пользователей.
    :param username: Имя пользователя.
    :param email: Адрес электронной почты.
    :return: Статус проверки по каждому критерию
    """
    result = {'username': True, 'email': True}
    for user in users:
        if user.username == username:
            result['username'] = False
        if user.email == email:
            result['email'] = False
    return result

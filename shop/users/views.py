from datetime import datetime
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from .autf import get_password_hash, create_access_token
from .depends import get_current_user, find_user_by_id, check_uniq, check_user
from .models import User
from .forms import CreatePassword, AdminUser, UpdateUser, SelectUser, Registration, RepairPassword


# Create your views here.
def add_user(request: WSGIRequest):
    """
    Регистрация нового пользователя.
    :param request: Запрос.
    :return: Переход на страницу пользователя при успешной регистрации или
    отображение регистрационной страницы.
    """
    info = {'title': 'Регистрация пользователя'}
    if request.method == 'POST':
        form = Registration(request.POST)
        if form.is_valid():
            if 'error' in info.keys():
                info.pop('error')
            # имя пользователя в системе
            username = form.cleaned_data['username']
            # адрес электронной почты
            email = form.cleaned_data['email']
            # возраст пользователя
            day_birth = form.cleaned_data['day_birth']
            password = form.cleaned_data['password']
            repeat_password = form.cleaned_data['repeat_password']

            users = User.objects.all()
            check = check_uniq(list(users), username, email)
            if not check['username']:
                info['message'] = f'Пользователь {username} уже существует!'
            elif password != repeat_password:
                info['message'] = f'Пароли не совпадают!'
            elif not check['email']:
                info['message'] = f'Пользователь c email: {email} уже существует!'
            else:
                password = get_password_hash(password)
                User.objects.create(username=username, day_birth=day_birth, email=email, password=password)
                user = User.objects.get(username=username)
                access_token = create_access_token({"sub": str(user.id)})
                response = HttpResponseRedirect(f'/user')
                response.set_cookie(key="users_access_token", value=access_token, httponly=True)
                return response
    form = Registration()
    info['form'] = form
    return render(request, 'users/registration.html', context=info)


def enter_user(request: WSGIRequest):
    """
    Вход в систему.
    :param request: Запрос.
    :return: Страница входа в систему или переадресация.
    """
    info = {'title': 'Вход'}
    if request.method == 'POST':
        form = SelectUser(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            info['message'], stat, user = check_user(username, password)
            if stat == 'Ok':
                access_token = create_access_token({"sub": str(user.id)})
                response = HttpResponseRedirect(f'/user')
                response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            else:
                response = render(request, "users/login.html", info)
            return response
    info['form'] = SelectUser()
    return render(request, "users/login.html", info)


def exit_user(request: WSGIRequest):
    """
    Выход из системы.
    :param request: Запрос.
    :return: Страница выхода из системы
    """
    info = {'title': 'Выход'}
    user = get_current_user(request)
    if request.method == 'POST':
        if user is not None:
            info['message'] = f'Пользователь: {user.username} вышел из системы'
            response = render(request, 'users/logout.html', info)
            response.delete_cookie(key="users_access_token")
            info['login'] = True
        else:
            info['message'] = 'Вы не были авторизованы'
            response = render(request, 'users/logout.html', info)
        return response
    if user is not None:
        info['login'] = True
    return render(request, 'users/logout.html', info)


def update_user(request: WSGIRequest, user_id: int = -1):
    """
    Изменение данных пользователя
    :param request: Запрос.
    :param user_id: Идентификатор пользователя.
    :return: Страница пользователя, страница с формой изменения данных пользователя.
    """
    info = {'title': 'Изменение данных пользователя'}
    user = get_current_user(request)
    if user is None:
        HttpResponseRedirect('/user/login')
    elif int(user_id) != user.id:
        return HttpResponse('Нет доступа')
    info['user'] = user
    if request.method == 'POST':
        form = UpdateUser(request.POST)
        # адрес электронной почты
        email = form.cleaned_data['email']
        # возраст пользователя
        day_birth = form.cleaned_data['day_birth']
        User.objects.filter(id=user_id).update(email=email, day_birth=day_birth, updated_at=datetime.now())
        info['message'] = 'Обновлено'
        return HttpResponseRedirect(f'/user')
    info['form'] = UpdateUser()
    return render(request, "users/update_user.html", info)


def delete_user_self(request: WSGIRequest):
    """
    Удаление пользователя
    :param request: Запрос.
    :return: Переадресация.
    """
    info = {'title': 'Удаление пользователя'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/main')
    User.objects.filter(id=user.id).update(is_active=False, updated_at=datetime.now())
    response = HttpResponseRedirect('/main')
    response.delete_cookie(key="users_access_token")
    return response


def select_user(request: WSGIRequest):
    """
    Отображение данных пользователя
    :param request: Запрос.
    :return: Страница с данными пользователя.
    """
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    print(user)
    info['display'] = 0
    if user is not None:
        info['user'] = user
        info['display'] = 1
    print(info)
    return render(request, "users/user_page.html", info)


def delete_user_admin(request: WSGIRequest, id_user: int):
    """
    Удаление данных пользователя из системы.
    :param request: Запрос.
    :param id_user: Идентификатор пользователя.
    :return:
    """
    info = {'title': 'Администратор. Удаление пользователя'}
    user = get_current_user(request)
    if user is None:
        return HttpResponse(content={'error': 'Вы не авторизованны'})
    elif not user.admin:
        return HttpResponse(content={'error': 'У вас отсутствуют права'})
    user = find_user_by_id(id_user)
    if user is None:
        return HttpResponse(content={'error': 'Пользователь не найден'})
    else:
        if request.method == 'POST':
            User.objects.filter(id=user.id).delete()
            return HttpResponseRedirect('user/list', status_code=303)

        info['user'] = user
        info['is_staff'] = user.admin
    return render(request, "users/delete_user_page.html", info)


def update_user_admin(request: WSGIRequest, id_user: int = -1):
    """
    Изменение данных пользователя администратором.
    :param request: Запрос.
    :param id_user: Идентификатор пользователя.
    :return: Страница выбранного пользователя или страница изменения данных пользователя.
    """
    info = {'title': 'Администратор. Изменение данных пользователя'}
    user = get_current_user(request)

    if user is None:
        return HttpResponse(content={'error': 'Вы не авторизованны или у вас отсутствуют права'})
    elif not user.admin:
        return HttpResponse(content={'error': 'Вы не авторизованны или у вас отсутствуют права'})

    user = find_user_by_id(id_user)
    if user is None:
        return HttpResponse(content={'error': 'Пользователь не найден'})
    else:
        if request.method == 'POST':
            form = AdminUser(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                day_birth = form.cleaned_data['day_birth']
                is_active = form.cleaned_data['is_active']
                is_staff = form.cleaned_data['is_staff']
                admin = form.cleaned_data['admin']
                bis_active, bis_staff, badmin = is_active == 'Да', is_staff == 'Да', admin == 'Да'
                User.objects.filter(id=id_user).update(email=email,
                                                       day_birth=day_birth,
                                                       is_active=bis_active,
                                                       is_staff=bis_staff, admin=badmin,
                                                       updated_at=datetime.now())
                return HttpResponseRedirect(f'/user/list/{id_user}')
        info['user'] = user
        info['form'] = AdminUser()
        return render(request, "users/update_admin_user.html", info)


def select_user_admin(request: WSGIRequest, id_user: int):
    """
    Данные выбранного пользователя.
    :param request: Запрос.
    :param id_user: Идентификатор пользователя.
    :return: Страница с данными пользователя.
    """
    info = {'title': 'Администратор. Данные пользователя'}
    user = get_current_user(request)
    if user is None:
        return HttpResponse(content={'Error': 'Вы не авторизованны'})
    elif user.admin is False:
        return HttpResponse(content={'Error': 'У вас отсутствуют права'})
    car_user = find_user_by_id(id_user)
    if car_user is None:
        return HttpResponse(content={'Error': 'Пользователь не найден'})
    else:
        info['user'] = car_user
    return render(request, "users/admin_user.html", info)


def select_list_user(request: WSGIRequest):
    """
    Список пользователей введённых в базу данных.
    :param request: Запрос.
    :return: Страница со списком пользователей.
    """
    info = {'title': 'Список пользователей'}
    user = get_current_user(request)
    if user is None:
        return HttpResponse(content={'error': 'вы не авторизованны. Пройдите авторизацию'})
    elif user.admin:
        users = User.objects.all()
        info['users'] = users
    return render(request, "users/users_list.html", info)


def repair_password(request: WSGIRequest):
    """
    Восстановление пароля пользователя.
    :param request: Запрос.
    :return: Страница восстановления пароля или создания нового пароля.
    """
    info = {'title': 'Восстановление пароля'}
    if request.method == 'POST':
        form = RepairPassword(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            user = User.objects.filter(username=username).first()
            if user is None or user.email != email:
                info['message'] = 'Пользователь не найден'
                return render(request, "users/repair.html", info)
            return HttpResponseRedirect(f'/user/create_password/{user.id}')
    info['form'] = RepairPassword()
    return render(request, "users/repair.html", info)


def create_password(request: WSGIRequest, user_id: int = -1):
    """
    Создание нового пароля.
    :param request: Запрос.
    :param user_id: Идентификатор пользователя.
    :return: Страница создания пароля или отображения данных пользователя.
    """
    info = {'title': 'Создание нового пароля'}
    user = User.objects.filter(id=user_id).first()
    if user is None:
        info['message'] = 'Пользователь не найден'
        return HttpResponseRedirect('/user')
    if request.method == 'POST':
        form = CreatePassword(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            repeat_password = form.cleaned_data['repeat_password']
            if password != repeat_password:
                info['message'] = 'Пароли не соответствуют'
                info['name'] = user.username
                info['user_id'] = user_id
                info['form'] = CreatePassword()
                return render(request, "users/create_new_password.html", info)
            password = get_password_hash(password)
            User.objects.filter(id=user.id).update(password=password, updated_at=datetime.now())
            info['message'] = 'Пароль изменён'
            access_token = create_access_token({"sub": str(user.id)})
            response = HttpResponseRedirect(f'/user')
            response.set_cookie(key="users_access_token", value=access_token, httponly=True)
            return response
    info['name'] = user.username
    info['user_id'] = user_id
    info['form'] = CreatePassword()
    return render(request, "users/create_new_password.html", info)


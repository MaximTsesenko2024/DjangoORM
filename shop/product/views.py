import math
import shutil
from datetime import datetime, date
from http.client import HTTPException
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from .depends import get_current_user, find_user_by_id
from .autf import verify_password, get_password_hash, create_access_token
from .models import User, Categories, ProductModel, BuyerProd, Shops
from .forms import Registration, SelectUser, UpdateUser, AdminUser, RepairPassword, CreatePassword, Product, \
    ProductUpdate
import base64
import os
from PIL import Image


class ProductView_list:
    """
    Описание отображения товара в списке
    """
    def __init__(self, name, price, id_prod, image_str, format_file):
        self.name = name
        self.price = price
        self.id = id_prod
        self.image_str = image_str
        self.format_file = format_file


class CarView:
    """
    Описание товара в корзине покупателя
    """
    def __init__(self, number, id_prod, name, price, count):
        self.number = number
        self.id_prod = id_prod
        self.name = name
        self.price = price
        self.count = count


cars = {}


# Create your views here.


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
            count = BuyerProd.filter(user=user.id).count()
            if count > 0:
                BuyerProd.filter(user=user.id).delete()
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


def image_to_str(product: Product, key: str):
    """
    Преобразование изображения в строку символов.
    :param product: Модель продукта для которого выполняется преобразование картинки в строку.
    :param key: Ключ определяющий размер картинки для отображения.
    :return: Строка символов соответствующая изображению переданному продукту.
    """
    if key == 'list':
        file_path = os.path.join("./product/templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join("./product/templates/product/image/" + product.name, product.img)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
    format_file = 'jpeg'
    return base64_encoded_image, format_file


def get_categories_subgroups(list_categories, id_category):
    """
    Получение списка подкатегорий для категории указанной идентификатором.
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Список категорий для которых указанный идентификатор является родительским
    """
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category):
    """
    Получение объекта категория по идентификатору
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Объект категория или None
    """
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def find_category(categories, id_category):
    """
    Вывод зависимости категорий для указанного идентификатора
    :param categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: строка представляющая цепочку родителей для указанной категории
    """
    if id_category is None or id_category == -1:
        return ''
    for category in categories:
        if category.id == id_category:
            if category.parent is None or category.parent == -1:
                return category.name
            else:
                return find_category(categories, category.parent) + ' / ' + category.name
    return ''


# Обработка таблицы Categories
# просмотр списка категорий
def list_categories(request: WSGIRequest):
    """
    Отображение списка категорий.
    :param request: Запрос.
    :return: Страница со списком категорий.
    """
    info = {'title': 'Список категорий'}
    curent_user = get_current_user(request)
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = Categories.objects.all()
        if categories is not None:
            info['categories'] = categories
    return render(request, 'product/categories_list.html', info)


# изменение категории
def update_category(request: WSGIRequest, id_category: int):
    """
    Изменение данных выбранной категории.
    :param request: Запрос.
    :return: Страница с данными категории или страница с формой изменения данных категории
    """
    info = {'title': 'Изменение данных категории'}
    id_category = int(id_category)
    parent = request.GET.get('parent', '')
    curent_user = get_current_user(request)
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    elif parent == '':
        info['display'] = 'Ok'
        categories = list(Categories.objects.all())
        category = get_category(categories, id_category)
        if category is None:
            return HttpResponse(content={'error': 'Категория не найдена'})
        info['category'] = category
        info['id_category'] = category.id
        info['categories'] = categories
    else:
        info['display'] = 'Ok'
        Categories.objects.filter(id=id_category).update(parent=int(parent))
        info['message'] = 'Обновлено'
        return HttpResponseRedirect(f'/product/category/{id_category}')
    return render(request, 'product/category_update.html', info)


# создание новой категории
def add_category(request: WSGIRequest):
    """
    Создание новой категории.
    :param request: Запрос.
    :return: Страница со списком категорий или с формой добавления категории.
    """
    info = {'title': 'Создание категории'}
    curent_user = get_current_user(request)
    name = request.GET.get('name', '')
    parent = request.GET.get('parent', '')
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '' and parent == '':
            categories = Categories.objects.all()
            if categories is not None:
                info['categories'] = categories
        elif name == '':
            info['message'] = 'Поле название не может быть пустым'
        elif parent == '':
            info['message'] = 'Поле родительская категория не может быть пустым'
        else:
            Categories.objects.create(name=name, parent=int(parent))
            return HttpResponseRedirect('/product/category/list')
    return render(request, 'product/category_create.html', info)


# удаление категории
def delete_category(request: WSGIRequest, id_category: int):
    """
    Удаление категории.
    :param request: Запрос.
    :param id_category: Идентификатор категории.
    :return: Страница удаления категории или список категорий
    """
    info = {'request': request, 'title': 'Удаление категории'}
    id_category = int(id_category)
    curent_user = get_current_user(request)
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            Categories.objects.filter(id=id_category).delete()
            return HttpResponseRedirect('/product/category/list')
        categories = list(Categories.objects.all())
        children = get_categories_subgroups(categories, id_category)
        info['id_category'] = id_category
        info['name'] = get_category(categories, id_category).name
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        else:
            info['delete'] = 1
    return render(request, 'product/category_delete.html', info)


# просмотр категории
def select_category(request: WSGIRequest, id_category: int):
    """
    Отображение данных выбранной категории.
    :param request: Запрос.
    :param id_category: Идентификатор категории.
    :return: Страница с данными выбранной категории.
    """
    info = {'title': 'Описание категории'}
    user = get_current_user(request)
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = list(Categories.objects.all())
        id_category = int(id_category)
        category = get_category(categories, id_category)
        if category is None:
            return HttpResponse(content={'error': 'Категория не найдена'})
        info['parent'] = get_category(categories, category.parent)
        info['children'] = get_categories_subgroups(categories, id_category)
        info['category'] = category
        info['categories'] = categories
    return render(request, 'product/category.html', info)


# Обработка таблицы Product
def select_products_list(request: WSGIRequest):
    """
    Отображение списка товаров с учётом выбранной категории и поисковой строкой
    :param request: Запрос.
    :return: Страница со списком товаров.
    """
    info = {'title': 'Список товаров'}
    user = get_current_user(request)
    category = request.GET.get('category', '')
    q = request.GET.get('q', '')
    if q is None:
        q = ''
    if category is None:
        category = ''
    if user is None:
        pass
    elif user.is_staff:
        info['is_staff'] = 'Ok'
    if q != '':
        querty = Q(name__icontains=q)
        querty = querty | Q(description__icontains=q)
        products = ProductModel.objects.filter(querty).all()
    elif category != '':
        products = ProductModel.objects.filter(category=int(category)).all()
    else:
        products = ProductModel.objects.all()
    if len(products) > 0:
        product_list = []
        for product in products:
            image_str, format_file = image_to_str(product, 'list')
            prod_item = ProductView_list(product.name, product.price, product.id, image_str, format_file)
            product_list.append(prod_item)
            paginator = Paginator(product_list, 4)
            page_number = request.GET.get('page', 1)
            try:
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            info['page_obj'] = page_obj
    return render(request, 'product/product_list_page.html', info)


# Создание нового продукты
def create_product(request: WSGIRequest):
    """
    Добавление нового товара.
    :param request: Запрос.
    :return: Страница с формой создания нового товара или переадресация на список товаров.
    """
    info = {'request': request, 'title': 'Добавление товара'}

    user = get_current_user(request)

    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['categories'] = list(Categories.objects.all())
        if request.method == 'POST':
            name = request.POST.get('name')
            item_number = request.POST.get('item_number')
            description = request.POST.get('description')
            price = float(request.POST.get('price'))
            count = int(request.POST.get('count'))
            category = request.POST.get('category')
            file = request.FILES['img']
            if name == '':
                info['message'] = 'Поле имя не может быть пустым'
                return render(request, 'product/add_product_page.html', info)
            try:
                if not os.path.exists("./product/templates/product/image/" + name):
                    os.mkdir("./product/templates/product/image/" + name)

                contents = file.read()
                file_name = file.name
                with open("./product/templates/product/image/" + name + '/' + file_name, "wb") as f:
                    f.write(contents)
            except Exception:
                raise HttpResponse(content={'error': 'Something went wrong'})
            finally:
                file.close()
            image = Image.open("./product/templates/product/image/" + name + '/' + file_name)
            image.thumbnail(size=(100, 100))
            image.save("./product/templates/product/image/" + name + '/small_' + file_name)
            ProductModel.objects.create(name=name, description=description,
                                        price=price, count=count,
                                        is_active=count > 0, category=Categories.objects.get(id=int(category)),
                                        item_number=item_number,
                                        img=file_name)
            return HttpResponseRedirect('/product/list')
    return render(request, 'product/add_product_page.html', info)


def update_product(request: WSGIRequest, id_product: int = -1):
    """
    Изменение данных о товаре.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :return:
    """
    info = {'title': 'Изменение описания товара'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/product/list')
    else:
        if request.method == 'POST':
            form = ProductUpdate(request.POST)
            if form.is_valid():
                description = form.cleaned_data['description']
                item_number = form.cleaned_data['item_number']
                price = float(form.cleaned_data['price'])
                count = int(form.cleaned_data['count'])
                category = form.cleaned_data['category']
                ProductModel.objects.filter(id=id_product).update(description=description,
                                                                  price=price, count=count,
                                                                  is_active=count > 0,
                                                                  category=int(category),
                                                                  item_number=item_number)

                return HttpResponseRedirect(f'/product/{id_product}')
    product = ProductModel.objects.get(id=id_product)
    info['categories'] = list(Categories.objects.all())
    info['product'] = product
    info['display'] = 'Ok'
    info['image_str'], info['format_file'] = image_to_str(product, 'page')
    return render(request, 'product/update_product_page.html', info)


def update_image_product(request: WSGIRequest, id_product: int = -1):
    """
    Изменение изображение для товара.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :return: Страница изменения изображения или страница с данными о товаре.
    """
    info = {'title': 'Изменение изображения товара'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/product/list')
    else:
        product = ProductModel.objects.get(id=id_product)
        if request.method == 'POST':
            file = request.FILES['img']
            try:
                if not os.path.exists("./product/templates/product/image/" + product.name):
                    os.mkdir("./product/templates/product/image/" + product.name)
                else:
                    os.remove("./product/templates/product/image/" + product.name + '/' + product.img)
                    os.remove("./product/templates/product/image/" + product.name + '/small_' + product.img)
                contents = file.read()
                file_name = file.name
                with open("./product/templates/product/image/" + product.name + '/' + file_name, "wb") as f:
                    f.write(contents)
            except Exception:
                raise HttpResponse(content={'error': 'Something went wrong'})
            finally:
                file.close()
            image = Image.open("./product/templates/product/image/" + product.name + '/' + file_name)
            image.thumbnail(size=(100, 100))
            image.save("./product/templates/product/image/" + product.name + '/small_' + file_name)
            ProductModel.objects.filter(id=id_product).update(img=file_name)
            return HttpResponseRedirect(f'/product/{id_product}')
    info['categories'] = list(Categories.objects.all())
    info['image_str'], info['format_file'] = image_to_str(product, 'page')
    info['product'] = product
    info['display'] = 'Ok'
    return render(request, 'product/update_image_product_page.html', info)


def delete_product(request: WSGIRequest, id_product: int = -1):
    """
    Удаление данных о товаре.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :return: Страница удаления товара или страница со списком товаров.
    """
    info = {'title': 'Удаление товара'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/product/list')
    else:
        if request.method == 'POST':
            product_use = BuyerProd.objects.filter(
                product=id_product).all()
            product = ProductModel.objects.filter(id=id_product).first()
            if product_use is None:
                shutil.rmtree("./product/templates/product/image/" + product.name)
                ProductModel.objects.filter(id=id_product).delete()
                return HttpResponseRedirect(f'/product/list')
            elif user.admin:
                BuyerProd.objects.filter(product=id_product).delete()
                shutil.rmtree("./product/templates/product/image/" + product.name)
                ProductModel.objects.filter(id=id_product).delete()
                return HttpResponseRedirect(f'/product/list')
            else:
                info['message'] = 'Товар уже покупали. Для удаления обратитесь к администратору'
                return render(request, 'delete_product_page.html', info)
        product = ProductModel.objects.filter(id=id_product).first()
        if product is None:
            return HttpResponseRedirect(f'/product/list')
        categories = list(Categories.objects.all())
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return render(request, 'product/delete_product_page.html', info)


def select_product(request: WSGIRequest, id_product: int = -1):
    """
    Отображение данных о товаре.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :return: Отображение данных о товаре.
    """
    info = {'request': request, 'title': 'Описание товара'}
    user = get_current_user(request)
    product = ProductModel.objects.filter(id=id_product).first()
    if product is not None:
        categories = list(Categories.objects.all())
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
    else:
        return HttpResponse(content={'error': 'Товар не найден'})
    return render(request, 'product/product_page.html', info)


def car(request: WSGIRequest, id_product: int = -1):
    """
    Добавление товара в корзину.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :return: Отображение страницы добавления товара в корзину.
    """
    info = {'title': 'Добавление товара в корзину'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect(f'/user/login')
    info['user'] = user
    product = ProductModel.objects.filter(id=id_product).first()
    if product is None:
        return HttpResponse(content={'error': 'Товар не найден'})
    if request.method == 'POST':
        count = int(request.POST.get('count'))
        if count < 1:
            info['message'] = 'Требуемое количество товара не может быть меньше 1'
        else:
            new_count = product.count - count
            if new_count < 0:
                info['message'] = 'Не достаточно товара'
                info['count'] = product.count
            else:
                ProductModel.objects.filter(id=id_product).update(count=new_count)
                product = ProductModel.objects.filter(id=id_product).first()
            info['product'] = product
            if user.id in cars.keys():
                number = len(cars[user.id])
            else:
                cars[user.id] = []
                number = 0
            car_prod = CarView(number, product.id, product.name, product.price, count)
            cars[user.id].append(car_prod)
            return render(request, 'product/car.html', info)
    info['product'] = product
    info['count'] = 1
    return render(request, 'product/car.html', info)


def buy(request: WSGIRequest):
    """
    Отображение корзины пользователя.
    :param request: Запрос.
    :return: Страница корзины пользователя.
    """
    info = {'title': 'Корзина товаров'}
    cost = 0
    user = get_current_user(request)
    delet = request.GET.get('delet')
    if delet is None:
        delet = -1
    else:
        delet = int(delet)
    shop = request.POST.get('shop', '')
    if shop is None:
        shop = ''
    if user.id not in cars.keys():
        info['message'] = 'Корзина пуста'
    else:
        car = cars[user.id]
        if delet > -1:
            for i in range(len(car)):
                if car[i].number == delet:
                    product = ProductModel.objects.filter(id=car[i].id_prod).first()
                    ProductModel.objects.filter(id=car[i].id_prod).update(count=product.count + car[i].count,
                                                                          is_active=True)
                    cars[user.id].pop(i)
                    break
        info['car'] = car
        info['user'] = user
        for item in car:
            cost += item.price * item.count
        info['cost'] = cost
        if request.method == 'POST':
            if shop == '':
                info['message'] = 'Выберите магазин'
                info['shops'] = Shops.objects.filter(is_active=True).all()
                return render(request, 'product/buy.html', info)
            return HttpResponseRedirect(f'/product/payment?shop={shop}')
        info['shops'] = Shops.objects.filter(is_active=True).all()
    return render(request, 'product/buy.html', info)


def payment(request: WSGIRequest):
    """
    Оплата товара
    :param request:
    :return: Страница оплаты товара
    """
    user = get_current_user(request)
    info = {'title': 'Оплата заказов'}
    shop = request.GET.get('shop')
    if user.id not in cars.keys():
        return HttpResponse('Корзина пуста')
    else:
        car = cars[user.id]
    if shop is None:
        shop = '-1'
    if request.method == 'POST':
        # list_buy_prod = BuyerProd.objects.all()
        # if len(list_buy_prod) < 1:
        #     max_operation = 1
        # else:
        #     max_operation = max(list(list_buy_prod), key='id_operation') + 1
        max_operation = BuyerProd.objects.aggregate(Max('id_operation', default=1))
        shop_sel = Shops.objects.get(id=int(shop))
        for item in car:
            prod = ProductModel.objects.get(id=item.id_prod)
            BuyerProd.objects.create(user=user, product=prod, id_operation=max_operation['id_operation__max'],
                                     id_shop=shop_sel)
        cars.pop(user.id)
        return HttpResponse(f'Спасибо за покупку. Заказ номер: {max_operation['id_operation__max']}')
    cost = 0
    info['car'] = car
    for item in car:
        cost += item.count * item.price
    info['cost'] = cost
    info['user'] = user
    shop = Shops.objects.get(id=int(shop))
    info['shop'] = shop
    return render(request, 'product/payment.html', info)


def create_shop(request: WSGIRequest):
    """
    Добавление нового магазина.
    :param request: Запрос.
    :return: Страница с формой добавления нового магазина или страница со списком магазинов.
    """
    info = {'request': request, 'title': 'Добавление магазина'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/main')
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            name = request.POST.get('name')
            location = request.POST.get('location')
            Shops.objects.create(name=name, location=location)
            return HttpResponseRedirect('/product/shop/list')
        return render(request, 'product/add_shop_page.html', info)


def update_shop(request: WSGIRequest, shop_id: int = -1):
    """
    Изменение данных о магазине.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :return: Страница с формой для изменения данных магазина или Страница с данными магазина.
    """
    info = {'title': 'Изменение данных магазина'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/main')
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            name = request.POST.get('name')
            location = request.POST.get('location')
            Shops.objects.filter(id=shop_id).update(name=name, location=location)
            return HttpResponseRedirect(f'/product/shop/{shop_id}')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/product/shop/list')
        info['shop'] = shop
        return render(request, 'product/update_shop_page.html', info)


def delete_shop(request: WSGIRequest, shop_id: int = -1):
    """
    Удаление данных о магазине из базы данных.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :return: Страница удаления магазина или страница со списком магазинов
    """
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/main')
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            Shops.objects.filter(id=shop_id).update(is_active=False)
            return HttpResponseRedirect('/product/shop/list')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/product/shop/list')
        info['shop'] = shop
        return render(request, 'product/delete_shop_page.html', info)


def select_shop_list(request: WSGIRequest):
    """
    Отображение списка магазинов.
    :param request: Запрос.
    :return: Страница со списком магазинов.
    """
    info = {'request': request, 'title': 'Список магазинов'}
    user = get_current_user(request)
    shops = Shops.objects.filter(is_active=True).all()
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return render(request, 'product/shop_list_page.html', info)


def select_shop(request: WSGIRequest, shop_id: int = -1):
    """
    Отображение данных выбранного магазина
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :return: Страница с данными магазина.
    """
    info = {'request': request, 'title': 'Данные магазина'}
    user = get_current_user(request)
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    shop = Shops.objects.filter(id=shop_id).first()
    if shop is None:
        return HttpResponseRedirect('/product/shop/list')
    info['shop'] = shop
    return render(request, 'product/shop_page.html', info)


def welcome(request: WSGIRequest, category: int = -1,
            q: str = ''):
    """
    Отображение главной страницы
    :param request: Запрос.
    :param category: Выбранная категория.
    :param q: Строка поиска.
    :return: Отображение главной страницы.
    """
    user = get_current_user(request)
    info = {'request': request, 'title': 'Главная страница'}
    info['name'] = 'Вход не выполнен'
    if user is not None:
        info['name'] = user.username
        info['is_staff'] = user.is_staff
        info['user_id'] = user.id
    else:
        info['name'] = 'Вход не выполнен'
    info['categories'] = Categories.objects.all()
    if category > -1 and q != '':
        return HttpResponseRedirect(f"/product/list?category={category}&q={q}")
    elif category > -1:
        return HttpResponseRedirect(f"/product/list?category={category}")
    elif q != '':
        return HttpResponseRedirect(f"/product/list?q={q}")
    return render(request, "product/main.html", info)

import math
from datetime import datetime, date
from http.client import HTTPException
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
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


class ProductView_list():
    def __init__(self, name, price, id_prod, image_str, format_file):
        self.name = name
        self.price = price
        self.id = id_prod
        self.image_str = image_str
        self.format_file = format_file


cars = {}


# Create your views here.


async def check_user(name: str, password: str, ):
    if name == '':
        return 'Имя пользователя не может быть пустым!', 'error', None
    user = User.objects.filter(username=name)
    if user is None:
        return 'Пользователь не найден.', 'error', user
    elif not verify_password(plain_password=password, hashed_password=user.password):
        return 'Пароль не верен!', 'error', user
    return 'Авторизованы', 'Ok', user


def check_uniq(users: list, username, email):
    result = {'username': True, 'email': True}
    for user in users:
        if user.username == username:
            result['username'] = False
        if user.email == email:
            result['email'] = False
    return result


def add_user(request: WSGIRequest):
    info = {'title': 'Добавление пользователя'}
    print(request.method)
    if request.method == 'POST':
        form = Registration(request.POST)
        if form.is_valid():
            print('valid')
            if 'error' in info.keys():
                info.pop('error')
            # имя пользователя в системе
            username = form.cleaned_data['username']
            # адрес электронной почты
            email = form.cleaned_data['email']
            # возраст пользователя
            day_birth = form.cleaned_data['day_birth']
            print(type(day_birth))
            #day_birth = datetime.strptime(day_birth, '%d-%m-%y').date()
            password = form.cleaned_data['password']
            repeat_password = form.cleaned_data['repeat_password']
            print('Данные получены')
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
                print('Сохранение')
                User.objects.create(username=username, day_birth=day_birth, email=email, password=password)
                user = User.objects.get(username=username)
                access_token = create_access_token({"sub": str(user.id)})
                response = HttpResponseRedirect(f'/user')
                response.set_cookie(key="users_access_token", value=access_token, httponly=True)
                return response

    user = get_current_user(request)
    info['message'] = user
    form = Registration()
    info['form'] = form
    return render(request, 'users/registration.html', context=info)


def enter_user(request: WSGIRequest):
    info = {'title': 'Вход'}
    if request.method == 'POST':
        form = SelectUser(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            info['message'], stat, user = check_user(username, password)
            print(info['message'], stat)
            if stat == 'Ok':
                access_token = create_access_token({"sub": str(user.id)})
                print(access_token)
                response = HttpResponseRedirect(f'/user')
                response.set_cookie(key="users_access_token", value=access_token, httponly=True)
                print('set token')
            else:
                response = render(request, "users/login.html", info)
            return response
    info['form'] = SelectUser()
    return render(request, "users/login.html", info)


def exit_user(request: WSGIRequest):
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
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    if user is None:
        HttpResponseRedirect('/user/login')
    elif user_id != user.id:
        return HTTPException(401, detail='Нет доступа')
    if request.method == 'POST':
        form = UpdateUser(request.POST)
        # адрес электронной почты
        email = form.cleaned_data['email']
        # возраст пользователя
        day_birth = form.cleaned_data['day_birth']
        User.objects.filter(id=user_id).update(email=email, day_birth=day_birth, updated_at=datetime.now())
        info['message'] = 'Обновлено'
        info['user'] = user
        return render(request, "users/update_user.html", info)
    info['form'] = UpdateUser()
    info['user'] = user
    return render(request, "users/update_user.html", info)


def delete_user_self(request: WSGIRequest):
    info = {'title': 'Удаление пользователя'}
    user = get_current_user(request)
    if user is not None:
        return HttpResponseRedirect('/main')
    User.objects.filter(id=user.id).update(is_active=False, updated_at=datetime.now())
    return HttpResponseRedirect('/main')


def select_user_get(request: WSGIRequest):
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    if user is not None:
        info['user'] = user
    return render(request, "users/user_page.html", info)


def delete_user_admin(request: WSGIRequest, id_user: int):
    info = {'title': 'Удаление пользователя'}
    user = get_current_user(request)
    if user is None:
        return HTTPException(status_code=404,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=404,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    user = find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=404, detail='Пользователь не найден')
    else:
        # if request.method == 'POST':
        #     buy_products = BuyerProd.filter(user=user.id)
        #     if buy_products is not None:
        #         BuyerProd.filter(user=user.id).delete()
        #     User.objects.filter(id=user.id).delete()
        #     return HttpResponseRedirect('user/list', status_code=303)

        info['user'] = user
        info['is_staff'] = user.admin
    return render(request, "users/user_page.html", info)


def update_user_admin(request: WSGIRequest, id_user: int = -1):
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    print(user.admin)
    if user is None:
        return HTTPException(status_code=404,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=404,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=404, detail='Пользователь не найден')
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
                return HttpResponseRedirect('/user/list')
        info['user'] = user
        info['form'] = AdminUser()
        return render(request, "users/update_admin_user.html", info)


def select_user_admin(request: WSGIRequest, id_user: int):
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    print(user.admin)
    if user is None:
        return HTTPException(status_code=404,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif user.admin is False:
        return HTTPException(status_code=404,
                             detail='У вас отсутствуют права')

    car_user = find_user_by_id(id_user)
    if car_user is None:
        return HTTPException(status_code=404, detail='Пользователь не найден')
    else:
        info['user'] = car_user
        info['is_staff'] = car_user.is_staff
    return render(request, "users/update_admin_user.html", info)


def select_list_user(request: WSGIRequest):
    info = {'title': 'Данные пользователя'}
    user = get_current_user(request)
    if user is None:
        return HTTPException(status_code=404,
                             detail='вы не авторизованны. Пройдите авторизацию')
    elif user.admin:
        users = User.objects.all()
        info['users'] = users
    return render(request, "users/users_list.html", info)


def repair_password_post(request: WSGIRequest):
    info = {'title': 'Востановление пароля'}
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
    info = {'title': 'Создание нового пароля'}
    user = User.odjects.filter(id=user_id)
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
    if key == 'list':
        file_path = os.path.join("./product/templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join("./product/templates/product/image/" + product.name, product.img)
    #print(os.path.exists(file_path), file_path)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
    format_file = 'jpeg'
    #print(base64_encoded_image)
    return base64_encoded_image, format_file


def get_categories_subgroups(list_categories, id_category):
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category):
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def find_category(categories, id_category):
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
def list_categories_get(request: WSGIRequest):
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


# отображение формы для изменения категории
def update_category_get(request: WSGIRequest):
    info = {'title': 'Обновление категории'}
    id_category = int(request.GET.get('id_category'))
    parent = request.GET.get('parent')
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
            return HTTPException(status_code=404, detail='Категория не найдена')
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
def add_category_get(request: WSGIRequest):
    info = {'title': 'Создание категории'}
    curent_user = get_current_user(request)
    name = request.GET.get('name')
    parent = request.GET.get('parent')
    print('create', name, parent)
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
def delete_category_get(request: WSGIRequest, id_category: int):
    info = {'request': request, 'title': 'Удаление категории'}
    curent_user = get_current_user(request)
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            Categories.filter(id=id_category).delete()
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
def category_get(request: WSGIRequest, id_category: int):
    info = {'title': 'Описание категории'}
    categories = list(Categories.objects.all())
    category = get_category(categories, id_category)
    if category is None:
        return HTTPException(status_code=404, detail='Категория не найдена')
    info['parent'] = get_category(categories, category.parent)
    info['children'] = get_categories_subgroups(categories, id_category)
    info['category'] = category
    info['categories'] = categories
    return render(request, 'product/category.html', info)


# Обработка таблицы Product
def select_products_list_get(request: WSGIRequest):
    info = {'title': 'Список товаров'}
    user = get_current_user(request)
    category = request.GET.get('category', '')
    q = request.GET.get('q', '')
    page = request.GET.get('page', '0')
    print(page)
    if q is None:
        q = ''
    if category is None:
        category = ''
    if page is None:
        page = 0
    else:
        page = int(page)
    if user is None:
        pass
    elif user.is_staff:
        info['is_staff'] = 'Ok'
    if q != '':
        print('Только имя', q)
        querty = Q(name__icontains=q)
        querty = querty | Q(description__icontains=q)
        print(querty)
        products = ProductModel.objects.filter(querty).all()
    elif category != '':
        products = ProductModel.objects.filter(category=int(category)).all()
    else:
        products = ProductModel.objects.all()
    if len(products) > 0:
        product_list = []
        for product in products:
            #print(product.name)
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
    info = {'request': request, 'title': 'Добавление товара'}

    #print(name, item_number, description, price, count, category, file.filename)
    user = get_current_user(request)
    print(user)
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['categories'] = list(Categories.objects.all())
        print('создание', request.method)
        if request.method == 'POST':
            name = request.POST.get('name')
            item_number = request.POST.get('item_number')
            description = request.POST.get('description')
            price = float(request.POST.get('price'))
            count = int(request.POST.get('count'))
            category = request.POST.get('category')
            # for filename, file in request.FILES.items():
            #     name_f = request.FILES[filename].name
            #     print(name_f)
            # file = request.FILES['btn-add_product']
            # file = None
            print(name, item_number, description)
            if name == '':
                info['message'] = 'Поле имя не может быть пустым'
                return render(request, 'product/add_product_page.html', info)
            # try:
            #     if not os.path.exists("./product/templates/product/image/" + name):
            #         os.mkdir("./product/templates/product/image/" + name)
            #
            #     contents = file.read()
            #     file_name = file.filename
            #     with open("./product/templates/product/image/" + name + '/' + file_name, "wb") as f:
            #         f.write(contents)
            # except Exception:
            #     raise HTTPException(status_code=500, detail='Something went wrong')
            # finally:
            #     file.close()
            # image = Image.open("./product/templates/product/image/" + name + '/' + file_name)
            # image.thumbnail(size=(100, 100))
            # image.save("./product/templates/product/image/" + name + '/small_' + file_name)
            if count > 0:
                bl = True
            else:
                bl = False
            ProductModel.objects.create(name=name, description=description,
                                        price=price, count=count,
                                        is_active=count > 0, category=int(category), item_number=item_number,
                                        img='')
            return HttpResponseRedirect('/product/list')
    return render(request, 'product/add_product_page.html', info)


def update_product(request: WSGIRequest, id_product: int = -1):
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
                product = ProductModel.objects.get(id=id_product)
                print(product.name)
                ProductModel.objects.get(id=id_product).update(description=description,
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
    return HttpResponseRedirect(f'/product/{id_product}')


def update_image_product(request: WSGIRequest, id_product: int = -1):
    info = {'title': 'Изменение описания товара'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/product/list')
    else:
        product = ProductModel.objects.get(id=id_product)
        if request.method == 'POST':
            file=request.FILES['img']
            try:
                if not os.path.exists("./product/templates/product/image/" + product.name):
                    os.mkdir("./product/templates/product/image/" + product.name)

                contents = file.read()
                file_name = file.name
                with open("./product/templates/product/image/" + product.name + '/' + file_name, "wb") as f:
                    f.write(contents)
            except Exception:
                raise HTTPException(status_code=500, detail='Something went wrong')
            finally:
                file.file.close()
            image = Image.open("./product/templates/product/image/" + product.name + '/' + file_name)
            image.thumbnail(size=(100, 100))
            image.save("./product/templates/product/image/" + product.name + '/small_' + file_name)
            ProductModel.objects.filter(id=id_product).update(img=file_name)
            return HttpResponseRedirect(f'/product/{id_product}')
    info['categories'] = list(Categories.objects.all())
    info['product'] = product
    info['display'] = 'Ok'
    #info['image_str'], info['format_file'] = image_to_str(product, 'page')
    #info['form']=ImageInput()
    return render(request, 'product/update_image_product_page.html', info)


def delete_product(request: WSGIRequest, id_product: int = -1):
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
                os.remove("./product/templates/product/image/" + product.name)
                ProductModel.objects.filter(id=id_product).delete()
                return HttpResponseRedirect(f'/product/list')
            elif user.admin:
                BuyerProd.objects.filter(product=id_product).delete()
                os.remove("./product/templates/product/image/" + product.name)
                ProductModel.objects.filter(id=id_product).delete()
            else:
                info['message'] = 'Товар уже покупали. Для удаления обратитесь к администратору'
                return render(request, 'delete_product_page.html', info)
        product = ProductModel.objects.filter(id=id_product).first()
        categories = list(Categories.objects.all())
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return render(request, 'product/delete_product_page.html', info)
    return HttpResponseRedirect(f'/product/list')


def select_product_get(request: WSGIRequest, id_product: int = -1):
    info = {'request': request, 'title': 'Описание товара'}
    user = get_current_user(request)
    product = ProductModel.objects.filter(id=id_product).first()
    if product is not None:
        categories = list(Categories.objects.all())
        info['product_category'] = find_category(categories, product.category)
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
    else:
        return HTTPException(404)
    return render(request, 'product/product_page.html', info)


def car_post(request: WSGIRequest, id_product: int = -1):
    info = {'title': 'Корзина'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect(f'/user/login')
    product = ProductModel.objects.filter(id=id_product).first()
    if product is None:
        return HTTPException(404, 'Товар не найден')
    if request.method == 'POST':
        count = int(request.POST.get('count'))
        if count < 1:
            info['message'] = 'Требуемое количество товара не может быть меньше 1'
        else:
            info['user'] = user
            new_count = product.count - count
            if new_count < 0:
                info['message'] = 'Не достаточно товара'
                info['count'] = product.count
            else:
                ProductModel.objects.filter(id=id_product).update(count=new_count)
                product = ProductModel.objects.filter(id=id_product).first()
            info['product'] = product
            if user.id in cars.keys():
                cars[user.id].append((product.id, product.name, product.price, count))
            else:
                cars[user.id] = [(product.id, product.name, product.price, count), ]
            return render(request, 'product/car.html', info)
        info['product'] = product
        info['user'] = user
        info['count'] = 1
        return render(request, 'product/car.html', info)
    return HttpResponseRedirect('/product/list')


def buy_post(request: WSGIRequest, user_id: int = -1):
    info = {'title': 'Оплата товара'}
    cost = 0
    user = get_current_user(request)
    delet = request.GET.get('delet')
    if delet is None:
        delet = -1
    else:
        delet = int(delet)
    shop = request.GET.get('shop')
    if shop is None:
        shop = ''
    if request.method == 'POST':

        car = cars[user_id]
        info['car'] = car
        info['user'] = user
        for item in car:
            cost += item[2] * item[3]
        info['cost'] = cost
        print(shop)
        if shop == '':
            info['message'] = 'Выберите магазин'
            return render(request, 'buy.html', info)
        else:
            if delet > -1:
                for i in range(len(cars[user_id])):
                    if cars[user_id][i][0] == delet:
                        product = ProductModel.objects.filter(id=delet).first()
                        ProductModel.objects.filter(id=delet).update(count=product.count + cars[user_id][i][3],
                                                                     is_active=True)
                        cars[user_id].pop(i)
            if user_id not in cars.keys():
                return HttpResponseRedirect('/product/list')
            car = cars[user_id]
            info['car'] = car
            info['user'] = user
            info['shops'] = Shops.objects.all()

            for item in car:
                cost += item[2] * item[3]
            info['cost'] = cost
            return render(request, 'product/buy.html', info)

    return HttpResponseRedirect(f'/product/payment/{user_id}?shop={shop}')


def payment_post(request: WSGIRequest, user_id: int = -1):
    user = get_current_user(request)
    info = {'title': 'Оплата заказов'}
    shop = request.GET.get('shop')
    if shop is None:
        shop = '-1'
    if request.method == 'POST':
        shop = request.POST.get('shop')
        if shop is None:
            shop = '-1'
        max_operation = BuyerProd.objects.all().max('id_operation')
        if max_operation is None:
            max_operation = 1
        else:
            max_operation = max_operation + 1
        shop_sel = Shops.objects.get(id=int(shop))
        for item in cars[user_id]:
            prod = ProductModel.objects.get(id=item[0])
            BuyerProd.objects.create(user=user, product=prod, id_operation=max_operation, id_shop=shop_sel)
        cars.pop(user_id)
        return HttpResponse('Спасибо за покупку')
    cost = 0
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    shop = Shops.objects.get(id=int(shop))
    info['shop'] = shop
    return render(request, 'payment.html', info)


def create_shop(request: WSGIRequest):
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


def update_shop_get(request: WSGIRequest, shop_id: int = -1):
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
            return HttpResponseRedirect('/product/shop/list')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/product/shop/list')
        info['shop'] = shop
        return render(request, 'product/update_shop_page.html', info)


def delete_shop_get(request: WSGIRequest, shop_id: int = -1):
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user/login')
    elif not user.is_staff:
        return HttpResponseRedirect('/main')
    else:
        info['display'] = 'Ok'
        if request.method == 'POST':
            Shops.objects.filter(id=shop_id).delete()
            return HttpResponseRedirect('/product/shop/list')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/product/shop/list')
        info['shop'] = shop
        return render(request, 'product/delete_shop_page.html', info)


def select_shop_list(request: WSGIRequest):
    info = {'request': request, 'title': 'Список магазинов'}
    user = get_current_user(request)
    shops = Shops.objects.all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return render(request, 'product/shop_list_page.html', info)


def select_shop_get(request: WSGIRequest, shop_id: int = -1):
    info = {'request': request, 'title': 'Данные магазина'}
    user = get_current_user(request)
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    shop = Shops.objects.filter(id=shop_id)
    if shop is None:
        return HttpResponseRedirect('/product/shop/list')
    info['shop'] = shop
    return render(request, 'product/shop_page.html', info)


def welcome(request: WSGIRequest, category: int = -1,
            q: str = ''):
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

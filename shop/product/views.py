import shutil
from datetime import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from users.depends import get_current_user
from .models import ProductModel
from .forms import Product, ProductUpdate
import base64
import os
from PIL import Image

from categories.depends import get_categories_list, get_category, find_category


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


# Create your views here.


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


# Обработка таблицы Product
def select_products_list(request: WSGIRequest):
    """
    Отображение списка товаров с учётом выбранной категории и поисковой строкой
    :param request: Запрос.
    :return: Страница со списком товаров.
    """
    info = {'title': 'Список товаров'}
    user = get_current_user(request)
    info['categories'] = get_categories_list()
    category = int(request.GET.get('category', '-1'))
    q = request.GET.get('q', '')
    if user is None:
        pass
    elif user.is_staff:
        info['is_staff'] = 'Ok'
    if q != '':
        querty = Q(name__icontains=q)
        querty = querty | Q(description__icontains=q)
        products = ProductModel.objects.filter(querty).all()
    elif category > -1:
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
    else:
        info['empty'] = True
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
        info['categories'] = get_categories_list()
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
                                        is_active=True,
                                        category=get_category(get_categories_list(), int(category)),
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
                active = form.cleaned_data['is_active']
                ProductModel.objects.filter(id=id_product).update(description=description,
                                                                  price=price, count=count,
                                                                  is_active=active == 'Да',
                                                                  category=int(category),
                                                                  item_number=item_number)

                return HttpResponseRedirect(f'/product/{id_product}')
    product = ProductModel.objects.get(id=id_product)
    info['categories'] = get_categories_list()
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
    info['categories'] = get_categories_list()
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
        product = ProductModel.objects.filter(id=id_product).first()
        if request.method == 'POST':
            ProductModel.objects.filter(id=id_product).delete()
            shutil.rmtree("./product/templates/product/image/" + product.name)
            return HttpResponseRedirect(f'/product/list')
        if product is None:
            return HttpResponseRedirect(f'/product/list')
        categories = get_categories_list()
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
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
    else:
        return HttpResponse(content={'error': 'Товар не найден'})
    return render(request, 'product/product_page.html', info)


def welcome(request: WSGIRequest):
    """
    Отображение главной страницы
    :param request: Запрос.
    :return: Отображение главной страницы.
    """
    user = get_current_user(request)
    info = {'request': request, 'title': 'Главная страница'}
    category = int(request.GET.get('category', '-1'))
    q = request.GET.get('q', '')
    if user is not None:
        info['name'] = user.username
        info['is_staff'] = user.is_staff
        info['user_id'] = user.id
    else:
        info['name'] = 'Вход не выполнен'
    info['categories'] = get_categories_list()
    if category > -1 and q != '':
        return HttpResponseRedirect(f"/product/list?category={category}&q={q}")
    elif category > -1:
        return HttpResponseRedirect(f"/product/list?category={category}")
    elif q != '':
        return HttpResponseRedirect(f"/product/list?q={q}")
    return render(request, "product/main.html", info)

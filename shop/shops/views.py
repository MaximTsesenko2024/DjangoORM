from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render
from users.depends import get_current_user
from .models import Shops


# Create your views here.
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
            return HttpResponseRedirect('/shops/list')
        return render(request, 'shops/add_shop_page.html', info)


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
            return HttpResponseRedirect(f'/shops/{shop_id}')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/shops/list')
        info['shop'] = shop
        return render(request, 'shops/update_shop_page.html', info)


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
            return HttpResponseRedirect('/shops/list')
        shop = Shops.objects.filter(id=shop_id).first()
        if shop is None:
            return HttpResponseRedirect('/shops/list')
        info['shop'] = shop
        return render(request, 'shops/delete_shop_page.html', info)


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
    return render(request, 'shops/shop_list_page.html', info)


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
        return HttpResponseRedirect('/shops/list')
    info['shop'] = shop
    return render(request, 'shops/shop_page.html', info)


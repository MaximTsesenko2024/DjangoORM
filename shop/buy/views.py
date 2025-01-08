from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from users.depends import get_current_user
from shops.depends import get_shop_list, get_shop
from product.depends import get_product, update_count_product

from .depends import order_list, get_product_list_by_order_number, get_order_list_by_user
from .models import BuyerProd


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
    product = get_product(id_product)
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
                update_count_product(id_product, -count)
                product.count = new_count
            info['product'] = product
            if user.id in cars.keys():
                number = len(cars[user.id])
            else:
                cars[user.id] = []
                number = 0
            car_prod = CarView(number, product.id, product.name, product.price, count)
            cars[user.id].append(car_prod)
            return render(request, 'buy/car.html', info)
    info['product'] = product
    info['count'] = 1
    return render(request, 'buy/car.html', info)


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
                    update_count_product(car[i].id_prod, car[i].count)
                    cars[user.id].pop(i)
                    break
        info['car'] = car
        info['user'] = user
        for item in car:
            cost += item.price * item.count
        info['cost'] = cost
        info['shops'] = get_shop_list()
        if request.method == 'POST':
            if shop == '':
                info['message'] = 'Выберите магазин'

                return render(request, 'buy/buy.html', info)
            return HttpResponseRedirect(f'/buy/payment?shop={shop}')
    return render(request, 'buy/buy.html', info)


def payment(request: WSGIRequest):
    """
    Оплата товара
    :param request:
    :return: Страница оплаты товара
    """
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/user')
    info = {'title': 'Оплата заказов'}
    shop = request.GET.get('shop')
    if user.id not in cars.keys():
        return HttpResponseRedirect('/main')
    else:
        car = cars[user.id]
    if shop is None:
        shop = '-1'
    if request.method == 'POST':
        max_operation = BuyerProd.objects.aggregate(Max('id_operation', default=0))
        number_operation = max_operation['id_operation__max'] + 1
        shop_sel = get_shop(int(shop))
        for item in car:
            prod = get_product(item.id_prod)
            BuyerProd.objects.create(user=user, product=prod, id_operation=number_operation,
                                     id_shop=shop_sel, count=item.count)
        cars.pop(user.id)
        info['message'] = f'Спасибо за покупку. Заказ номер: {number_operation}'
        return render(request, 'buy/payment.html', info)
    cost = 0
    info['car'] = car
    for item in car:
        cost += item.count * item.price
    info['cost'] = cost
    info['user'] = user
    info['shop'] = get_shop(int(shop))
    info['display'] = True
    return render(request, 'buy/payment.html', info)


def select_order_list(request: WSGIRequest, user_id: int):
    """
    Отображение истории заказов пользователя
    :param user_id: Идентификатор пользователя
    :param request: Запрос.
    :return: Страница со списком заказов.
    """
    info = {'title': 'История заказов'}
    user = get_current_user(request)
    number = request.GET.get('number', '-1')
    user_id = int(user_id)
    try:
        number = int(number)
    except Exception:
        number = -1
    if user is None:
        return HttpResponseRedirect('/main')
    elif not user.admin and user.id != user_id:
        info['message'] = 'Нет доступа'
    else:
        info['display'] = True
        if number > -1:
            orders = get_product_list_by_order_number(number)
        else:
            orders = get_order_list_by_user(user_id)
        if len(orders) > 0:
            orders_list = order_list(orders)
            paginator = Paginator(orders_list, 4)
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
    return render(request, 'buy/order_list_page.html', info)


def find_order_page(request: WSGIRequest):
    """
    Страница поиска заказа (только для сотрудников)
    :param request: Запрос
    :return: Страница с полем для запроса
    """
    info = {'title': 'Поиск заказа'}
    user = get_current_user(request)
    number = request.GET.get('number', '-1')
    try:
        number = int(number)
    except Exception:
        number = -1
    if user is None:
        return HttpResponseRedirect('/main')
    elif not user.is_staff:
        return HttpResponseRedirect(f'/buy/order/{user.id}')
    info['display'] = True
    if number > -1:
        return HttpResponseRedirect(f'/buy/order/number/{number}')
    else:
        return render(request, 'buy/order_find_page.html', info)


def get_select_order(request: WSGIRequest, number: int):
    """
    Отображение заказа
    :param request: Запрос
    :param number: Номер заказа
    :return: Страница заказа
    """
    info = {'title': 'Описание заказа'}
    user = get_current_user(request)
    if user is None:
        return HttpResponseRedirect('/main')
    elif user.is_staff:
        info['is_staff'] = '1'
    number = int(number)
    info['display'] = True
    order_prod_list = get_product_list_by_order_number(number)
    order = order_list(order_prod_list)
    if order_prod_list is None:
        info['message'] = 'Заказ не найден'
    else:
        info['order'] = order
        if order.used:
            info['message'] = 'Заказ выдан'
        else:
            info['used'] = True
    used = request.GET.get('used', '')
    if used:
        BuyerProd.objects.filter(id_operation=number).update(is_used=True)
    return render(request, 'buy/order_page.html', info)

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .depends import get_categories_list, get_category, get_categories_subgroups
from .models import Categories
from users.depends import get_current_user


# Create your views here.
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
        categories = get_categories_list()
        if categories is not None:
            info['categories'] = categories
    return render(request, 'categories/categories_list.html', info)


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
        categories = get_categories_list()
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
        return HttpResponseRedirect(f'/category/{id_category}')
    return render(request, 'categories//category_update.html', info)


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
            categories = get_categories_list()
            if categories is not None:
                info['categories'] = categories
        elif name == '':
            info['message'] = 'Поле название не может быть пустым'
        elif parent == '':
            info['message'] = 'Поле родительская категория не может быть пустым'
        else:
            Categories.objects.create(name=name, parent=int(parent))
            return HttpResponseRedirect('/categories/list')
    return render(request, 'categories/category_create.html', info)


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
            return HttpResponseRedirect('/categories/list')
        categories = get_categories_list()
        children = get_categories_subgroups(categories, id_category)
        info['id_category'] = id_category
        info['name'] = get_category(categories, id_category).name
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        else:
            info['delete'] = 1
    return render(request, 'categories/category_delete.html', info)


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
    return render(request, 'categories/category.html', info)

from .models import Categories

def get_categories_list():
    """
    Получение списка категорий введённых в базу
    :return: Список категорий
    """
    categories = Categories.objects.all()
    if categories is not None:
        categories = list(categories)
    return categories

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

from .models import Shops


def get_shop(shop_id: int) -> Shops | None:
    """
    Получение объекта магазин по его идентификатору
    :param shop_id: Идентификатор объекта магазин
    :return: объект магазин или None
    """
    return Shops.objects.filter(is_active=True, id=shop_id).first()


def get_shop_list() -> list:
    """
    Получение списка доступных магазинов
    :return: Список магазинов
    """
    shop_list = Shops.objects.filter(is_active=True).all()
    if shop_list is not None:
        shop_list = list(shop_list)
    return shop_list
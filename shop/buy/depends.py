from .models import BuyerProd

class Order:
    """
    Описание заказа
    """

    def __init__(self, number, used, shop):
        self.number = number
        self.used = used
        self.shop = shop
        self.prod_list = []

    def add_prod(self, product, count):
        """
        Добавление товара
        :param count: Количество товара
        :param product: Товар
        """
        self.prod_list.append((product, count))

def get_product_list_by_order_number(number:int):
    """
    Получение списка товаров по номеру заказа
    :param number: номер заказа
    :return: список товаров
    """
    buyer_prods = BuyerProd.objects.filter(id_operation=number).all()
    if buyer_prods is None:
        return None
    else:
        return list(buyer_prods)


def get_order_list_by_user(user_id: int):
    """
    Получение списка заказов по идентификатору пользователя
    :param user_id: идентификатор пользователя
    :return: список заказов
    """
    order_list = BuyerProd.objects.filter(user=user_id).order_by('-id_operation')
    if order_list is None:
        return None
    else:
        return list(order_list)

def order_list(buy_prods: list):
    """
    Создание списка заказов
    :return: список заказов
    """
    orders_list = []
    orders_list.append(Order(buy_prods[0].id_operation, buy_prods[0].is_used, buy_prods[0].id_shop))
    for i in range(len(buy_prods)):
        if buy_prods[i].id_operation != orders_list[-1].number:
            orders_list.append(Order(buy_prods[i].id_operation, buy_prods[i].is_used, buy_prods[i].id_shop))
        orders_list[-1].add_prod(buy_prods[i].product, buy_prods[i].count)
    return orders_list


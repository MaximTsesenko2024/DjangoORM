from .models import ProductModel


def get_product(product_id: int) -> ProductModel | None:
    """
    Получение объекта продукт по идентификатору
    :param product_id: идентификатор объекта продукт
    :return: объекта продукт или None
    """
    return ProductModel.objects.filter(id=product_id).first()


def update_count_product(product_id: int, update_count: int) -> bool:
    """
    Изменение количества товара
    :param product_id: Идентификатор товара.
    :param update_count: Изменение количества + увеличение, - уменьшение.
    :return статус операции
    """
    product = ProductModel.objects.filter(id=product_id).first()
    ProductModel.objects.filter(id=product_id).update(count=product.count+update_count)
    return True

from django.db import models


# Create your models here.


class ProductModel(models.Model):
    """
    Модель товара в системе
    """
    # наименование товара
    name = models.CharField(max_length=256)
    # Описание товара
    description = models.TextField()
    # артикул товара
    item_number = models.CharField(max_length=256)
    # стоимость товара
    price = models.FloatField()
    # доступное количество товара
    count = models.IntegerField()
    # признак наличия товара
    is_active = models.BooleanField(default=True)
    # участие в акции
    action = models.BooleanField(default=False)
    # картинка товара
    img = models.CharField(max_length=255)
    # категория товаров
    category = models.ForeignKey('categories.Categories', on_delete=models.CASCADE)

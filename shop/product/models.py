from django.db import models


# Create your models here.
class User(models.Model):
    """
    Модель пользователя в системе
    """
    # имя пользователя в системе
    username = models.CharField(max_length=255, unique=True)
    # адрес электронной почты
    email = models.CharField(max_length=255, unique=True)
    # дата рождения
    day_birth = models.DateField()
    password = models.TextField()
    # Флаг активности пользователя
    is_active = models.BooleanField(default=True)
    # Флаг принадлежности к сотрудникам
    is_staff = models.BooleanField(default=False)
    # Флаг принадлежности к администраторам
    admin = models.BooleanField(default=False)
    # Временная метка создания объекта.
    created_at = models.DateTimeField(auto_now_add=True)
    # Временная метка показывающая время последнего обновления объекта.
    updated_at = models.DateTimeField(auto_now=True)


class Categories(models.Model):
    """
    Модель категории товара в системе
    """
    name = models.CharField(max_length=255, unique=True)
    parent = models.IntegerField(default=-1)


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
    category = models.ForeignKey('Categories', on_delete=models.CASCADE)


class Shops(models.Model):
    """
    Модель магазина в системе
    """
    name = models.CharField(max_length=255, unique=True)
    location = models.TextField()
    is_active = models.BooleanField(default=True)


class BuyerProd(models.Model):
    """
    Модель покупки товара
    """
    id_operation = models.IntegerField(null=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    product = models.ForeignKey('ProductModel', on_delete=models.CASCADE)
    id_shop = models.ForeignKey('Shops', on_delete=models.CASCADE)

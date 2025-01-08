from django.db import models
from product.models import ProductModel
from users.models import User
from shops.models import Shops


# Create your models here.

class BuyerProd(models.Model):
    """
    Модель покупки товара
    """
    id_operation = models.IntegerField(null=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    product = models.ForeignKey('product.ProductModel', on_delete=models.CASCADE)
    id_shop = models.ForeignKey('shops.Shops', on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    count = models.IntegerField()


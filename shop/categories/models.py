from django.db import models


# Create your models here.
class Categories(models.Model):
    """
    Модель категории товара в системе
    """
    name = models.CharField(max_length=255, unique=True)
    parent = models.IntegerField(default=-1)

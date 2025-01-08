from django.db import models


# Create your models here.
class Shops(models.Model):
    """
    Модель магазина в системе
    """
    name = models.CharField(max_length=255, unique=True)
    location = models.TextField()
    is_active = models.BooleanField(default=True)

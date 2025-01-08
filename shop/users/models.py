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
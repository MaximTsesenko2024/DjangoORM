from django import forms
from .models import User
from datetime import date



class AdminUser(forms.Form):
    # адрес электронной почты
    email = forms.CharField(max_length=255)
    # дата рождения
    day_birth = forms.DateField()
    # Флаг активности пользователя
    is_active = forms.CharField(max_length=255)
    # Флаг принадлежности к сотрудникам
    is_staff = forms.CharField(max_length=255)
    # Флаг принадлежности к администраторам
    admin = forms.CharField(max_length=255)

class Registration(forms.Form):
    username = forms.CharField(max_length=255)
    email = forms.CharField(max_length=255)
    day_birth = forms.DateField()
    password = forms.CharField(max_length=255)
    repeat_password = forms.CharField(max_length=255)


class SelectUser(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255)


class UpdateUser(forms.Form):
    email = forms.CharField(max_length=255)
    day_birth = forms.DateField()


class RepairPassword(forms.Form):
    username = forms.CharField(max_length=255)
    email = forms.CharField(max_length=255)


class CreatePassword(forms.Form):
    password = forms.CharField(max_length=255)
    repeat_password = forms.CharField(max_length=255)
    
    
class Product(forms.Form):
    name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    price = forms.FloatField()
    count = forms.IntegerField()
    item_number = forms.CharField(max_length=255)
    category = forms.IntegerField()


class Car(forms.Form):
    count = forms.IntegerField()


class Buyer(forms.Form):
    user = forms.IntegerField()
    product = forms.IntegerField()
    shop = forms.CharField(max_length=255)


class Category(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(max_length=255)
    parent = forms.IntegerField()


class Shop(forms.Form):
    name = forms.CharField(max_length=255)
    location = forms.CharField(max_length=255)

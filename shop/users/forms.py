from django import forms
from .models import User


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
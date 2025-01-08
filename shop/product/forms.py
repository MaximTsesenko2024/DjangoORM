from django import forms
from .models import ProductModel
from datetime import date


class Product(forms.Form):
    name = forms.CharField(max_length=255)
    description = forms.CharField(max_length=255)
    price = forms.FloatField()
    count = forms.IntegerField()
    item_number = forms.CharField(max_length=255)
    category = forms.IntegerField()
    img = forms.CharField(max_length=255)


class ProductUpdate(forms.Form):
    description = forms.CharField(max_length=255)
    price = forms.FloatField()
    count = forms.IntegerField()
    item_number = forms.CharField(max_length=255)
    category = forms.IntegerField()
    is_active = forms.CharField(max_length=255)



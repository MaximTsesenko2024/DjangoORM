from django import forms


class Shop(forms.Form):
    name = forms.CharField(max_length=255)
    location = forms.CharField(max_length=255)

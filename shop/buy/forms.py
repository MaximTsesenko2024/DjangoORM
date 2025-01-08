from django import forms


class Buyer(forms.Form):
    user = forms.IntegerField()
    product = forms.IntegerField()
    shop = forms.CharField(max_length=255)


class Car(forms.Form):
    count = forms.IntegerField()

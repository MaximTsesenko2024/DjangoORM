from django import forms


class Category(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(max_length=255)
    parent = forms.IntegerField()

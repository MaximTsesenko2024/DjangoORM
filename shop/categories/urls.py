from django.contrib import admin
from django.urls import path
from .views import list_categories, update_category, add_category, delete_category, select_category

urlpatterns = [
    path('list', list_categories),
    path('update/<id_category>', update_category),
    path('create', add_category),
    path('delete/<id_category>', delete_category),
    path('<id_category>', select_category),
    ]

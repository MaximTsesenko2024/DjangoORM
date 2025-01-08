from django.contrib import admin
from django.urls import path
from .views import create_shop, update_shop, delete_shop, select_shop_list, select_shop

urlpatterns = [
    path('create', create_shop),
    path('update/<shop_id>', update_shop),
    path('delete/<shop_id>', delete_shop),
    path('list', select_shop_list),
    path('<shop_id>', select_shop),
    ]

from django.contrib import admin
from django.urls import path
from .views import select_products_list, create_product, update_product, update_image_product, delete_product, \
    select_product

urlpatterns = [
    path('list', select_products_list),
    path('create', create_product),
    path('update_product/<id_product>', update_product),
    path('update_image_product/<id_product>', update_image_product),
    path('delete/<id_product>', delete_product),
    path('<id_product>', select_product),
    ]

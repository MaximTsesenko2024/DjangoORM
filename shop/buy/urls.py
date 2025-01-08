from django.contrib import admin
from django.urls import path
from .views import car, buy, payment, get_select_order, select_order_list, find_order_page

urlpatterns = [
    path('car/<id_product>', car),
    path('buy', buy),
    path('payment', payment),
    path('order/number/<number>', get_select_order),
    path('order/<user_id>', select_order_list),
    path('order', find_order_page),
    ]

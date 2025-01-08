from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('registration', add_user),
    path('login', enter_user),
    path('logout', exit_user),
    path('update/<user_id>', update_user),
    path('delete', delete_user_self),
    path('list/delete/<id_user>', delete_user_admin),
    path('list/update/<id_user>', update_user_admin),
    path('list/<id_user>', select_user_admin),
    path('list', select_list_user),
    path('repair', repair_password),
    path('create_password/<user_id>', create_password),
    path('', select_user),
    ]

"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from product.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', welcome),
    path('user/registration', add_user),
    path('user/login', enter_user),
    path('user/logout', exit_user),
    path('user/update/<user_id>', update_user),
    path('user/delete',delete_user_self),
    path('user/list/delete/<id_user>', delete_user_admin),
    path('user/list/update/<id_user>', update_user_admin),
    path('user/list/<id_user>', select_user_admin),
    path('user/list', select_list_user),
    path('user/repair', repair_password),
    path('user/create_password/<user_id>', create_password),
    path('user/', select_user),
    path('product/category/list', list_categories),
    path('product/category/update/<id_category>', update_category),
    path('product/category/create', add_category),
    path('product/category/delete/<id_category>', delete_category),
    path('product/category/<id_category>', select_category),
    path('product/car/<id_product>', car),
    path('product/buy', buy),
    path('product/payment', payment),
    path('product/shop/create', create_shop),
    path('product/shop/update/<shop_id>',update_shop),
    path('product/shop/delete/<shop_id>', delete_shop),
    path('product/shop/list', select_shop_list),
    path('product/shop/<shop_id>', select_shop),
    path('product/list', select_products_list),
    path('product/create', create_product),
    path('product/update_product/<id_product>', update_product),
    path('product/update_image_product/<id_product>', update_image_product),
    path('product/delete/<id_product>', delete_product),
    path('product/<id_product>', select_product),
    path('/', welcome),
]

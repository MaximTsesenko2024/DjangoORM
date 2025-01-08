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
from django.urls import path, include
from users.urls import urlpatterns as user_url
from shops.urls import urlpatterns as shop_url
from product.urls import urlpatterns as product_url
from product.views import welcome
from categories.urls import urlpatterns as categories_url
from buy.urls import urlpatterns as buy_url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', welcome),
    path('user/', include(user_url)),
    path('shops/', include(shop_url)),
    path('product/', include(product_url)),
    path('categories/', include(categories_url)),
    path('buy/', include(buy_url)),
    path('', welcome),
]

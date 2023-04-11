"""
URL configuration for orders_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from backend.views import (
    BasketView,
    CategoryListView,
    ContactView,
    DetailUpdateUser,
    LoginUser,
    PartnerOrderListView,
    PartnerStatus,
    PartnerUpdate,
    ProductInfoListView,
    RegisterUser,
    ShopListView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/register', RegisterUser.as_view(), name='reg-user'),
    path('user/login', LoginUser.as_view(), name='login-user'),
    path('user/<int:pk>', DetailUpdateUser.as_view(), name='detail-user'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('categories', CategoryListView.as_view(), name='categories'),
    path('shops', ShopListView.as_view(), name='shops'),
    path('products', ProductInfoListView.as_view(), name='products'),
    path('basket', BasketView.as_view(), name='basket'),
    path('partner/status', PartnerStatus.as_view(), name='partner-status'),
    path('partner/orders', PartnerOrderListView.as_view(), name='partner-orders'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
]

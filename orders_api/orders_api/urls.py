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
from django.urls import include, path
from backend.views import (
    BasketView,
    CategoryListView,
    ConfirmEmailView,
    ContactView,
    DetailUpdateUser,
    LoginUser,
    OrderView,
    PartnerOrderListView,
    PartnerStatus,
    PartnerUpdate,
    ProductInfoListView,
    RegisterUser,
    ShopListRetrieveViewSet,
    # ShopListView
)
from django_rest_passwordreset.views import (
    reset_password_request_token,
    reset_password_confirm
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'shops', ShopListRetrieveViewSet, basename='shop')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('user/register', RegisterUser.as_view(), name='reg-user'),
    path('user/register/confirm', ConfirmEmailView.as_view(), name='reg-user-confirm'),
    path('user/login', LoginUser.as_view(), name='login-user'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user', DetailUpdateUser.as_view(), name='detail-user'),
    path('user/password/reset', reset_password_request_token, name='password-reset'),
    path('user/password/reset/confirm', reset_password_confirm, name='password-reset-confirm'),

    path('categories', CategoryListView.as_view(), name='categories'),
    # path('shops', ShopListView.as_view(), name='shops'),
    path('products', ProductInfoListView.as_view(), name='products'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/status', PartnerStatus.as_view(), name='partner-status'),
    path('partner/orders', PartnerOrderListView.as_view(), name='partner-orders'),
    
    path('accounts/', include('allauth.urls'), name='accounts'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('', include(router.urls)),
]

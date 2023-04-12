from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('shop', 'Магазин'),
        ('buyer', 'Покупатель'),
    )

    # REQUIRED_FIELDS = []
    # USERNAME_FIELD = 'email'

    email = models.EmailField(max_length=255, unique=True)
    type = models.CharField(
        max_length=5,
        choices=USER_TYPE_CHOICES,
        default='buyer'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='backend_users',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='backend_users',
    )
    is_active = models.BooleanField(default=False)
    # tokens = models.ForeignKey(
    #     Token,
    #     on_delete=models.CASCADE,
    #     related_name='owner'
    # )


# class Token(Token):
#     # pass
#     owner = models.ForeignKey(
#         User,
#         related_name='auth_tokens',
#         on_delete=models.CASCADE,
#     )
    # created = models.DateTimeField(auto_now_add=True)


class Shop(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        User,
        related_name='shop',
        on_delete=models.CASCADE
    )
    url = models.URLField(default='')
    filename = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    shops = models.ManyToManyField(
        Shop,
        related_name='categories'
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    external_id = models.PositiveIntegerField()
    product = models.ForeignKey(
        Product,
        related_name='product_infos',
        on_delete=models.CASCADE
    )
    shop = models.ForeignKey(
        Shop,
        related_name='product_infos',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    model = models.CharField()
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    price_rrc = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        related_name='product_parameters',
        on_delete=models.CASCADE
    )
    parameter = models.ForeignKey(
        Parameter,
        related_name='product_parameters',
        on_delete=models.CASCADE
    )
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value


class Order(models.Model):
    STATE_CHOICES = (
        ('basket', 'Статус корзины'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )
    
    user = models.ForeignKey(
        User,
        related_name='orders',
        on_delete=models.CASCADE
    )
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=255,
        choices=STATE_CHOICES,
        default='basket'
    )

    def __str__(self):
        return f'Order {self.pk} ({self.user.username})'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    # product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product_info = models.ForeignKey(
        ProductInfo,
        related_name='ordered_items',
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField()

    def __str__(self):
        return f'{self.product} ({self.quantity})'


class Contact(models.Model):
    TYPE_CHOICES = (
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('address', 'Address'),
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    user = models.ForeignKey(
        User,
        related_name='contact',
        on_delete=models.CASCADE
    )
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value


class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(
        User,
        related_name='confirm_email',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    token = models.CharField(max_length=64, unique=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(length=64)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"

import time
import pytest
from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from model_bakery import baker
import yaml

from backend.models import (
    Category,
    ConfirmEmailToken,
    Contact,
    Order,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
    Parameter
)
from backend.serializers import OrderSerializer, ShopSerializer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='admin',
        email='test@example.com',
        password='testpassword'
    )


@pytest.mark.django_db
class TestRegisterUser:

    def test_successful_registration(self, api_client):
        url = reverse('reg-user')
        data = {
            'username': 'testuser',
            'email': 'test@mail.ru',
            'password': 'testpassword'
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_registration_with_missing_field(self, api_client):
        url = reverse('reg-user')
        data = {'username': 'testuser'}

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_registration_with_existing_username(self, api_client, user):
        url = reverse('reg-user')
        data = {
            'username': user.username,
            'email': 'test@mail.ru',
            'password': 'testpassword'
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert response.data['username'][0].code == 'unique'

    def test_registration_with_existing_email(self, api_client, user):
        url = reverse('reg-user')
        data = {
            'username': 'testuser',
            'email': user.email,
            'password': 'testpassword'
        }

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        assert response.data['email'][0].code == 'unique'


@pytest.mark.django_db
class TestLoginUser:

    def test_login_user_success(self, api_client, user):
        url = reverse('login-user')
        data = {'email': user.email, 'password': 'testpassword'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

    def test_login_user_invalid_credentials(self, api_client, user):
        url = reverse('login-user')
        data = {'email': user.email, 'password': 'wrongpassword'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data

    def test_login_user_missing_credentials(self, api_client, user):
        url = reverse('login-user')
        data = {'email': user.email}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


class TestRetrieveUpdateUser(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass'
        )
        self.url = reverse('detail-user')
        
    def test_retrieve_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user(self):
        self.client.force_authenticate(user=self.user)
        data = {'username': 'newusername'}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], data['username'])


class TestCategoryList(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.catergories = baker.make(Category, _quantity=10)

    def test_category_list_view(self):
        url = reverse('categories')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), Category.objects.count())

        expected_fields = {'id', 'name', 'shops'}
        for category in response.data:
            self.assertEqual(set(category.keys()), expected_fields)


class TestShopListRetrieveViewSet(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.shops = baker.make(Shop, _quantity=5)

    def test_list_shops(self):
        response = self.client.get('/shops/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_retrieve_shop(self):
        shop_id = self.shops[0].id
        response = self.client.get(f'/shops/{shop_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], shop_id)


class TestProductInfoListView(APITestCase):
    def setUp(self):
        self.url = reverse('products')
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass'
        )
        self.shop = baker.make(Shop, user=self.user)
        self.category = baker.make(Category)
        self.category.shops.add(self.shop)
        self.product = baker.make(Product, category=self.category)
        self.parameter = baker.make(Parameter)
        self.product_info = baker.make(
            ProductInfo, product=self.product, shop=self.shop
        )
        self.product_parameter = baker.make(
            ProductParameter,
            product_info=self.product_info,
            parameter=self.parameter
        )

    def test_get_product_info_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.product_info.id)

    def test_filter_by_shop_id(self):
        another_product_info = baker.make(ProductInfo)
        response = self.client.get(
            self.url, {'shop_id': self.product_info.shop_id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.product_info.id)

    def test_filter_by_product_category_id(self):
        another_category = baker.make(Category)
        another_product = baker.make(Product, category=another_category)
        another_product_info = baker.make(ProductInfo, product=another_product)
        response = self.client.get(
            self.url, {'product__category_id': self.category.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.product_info.id)

    def test_order_by_price(self):
        another_product_info = baker.make(
            ProductInfo, price=self.product_info.price + 100
        )
        response = self.client.get(self.url, {'ordering': 'price'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], self.product_info.id)
        self.assertEqual(response.data[1]['id'], another_product_info.id)

    def test_order_by_quantity(self):
        another_product_info = baker.make(ProductInfo, quantity=10)
        response = self.client.get(self.url, {'ordering': 'quantity'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], another_product_info.id)
        self.assertEqual(response.data[1]['id'], self.product_info.id)

    def test_search_by_product_name(self):
        response = self.client.get(self.url, {'search': self.product.name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.product_info.id)

    def test_search_by_category_name(self):
        response = self.client.get(self.url, {'search': self.category.name})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.product_info.id)


class TestBasketView(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('basket')
        self.user = baker.make(User)
        self.shop = baker.make(Shop, user=self.user)
        self.category = baker.make(Category)
        self.product = baker.make(Product, category=self.category)
        self.product_info = baker.make(
            ProductInfo, product=self.product, shop=self.shop
        )
        self.order = baker.make(
            Order, user=self.user,
        )
        self.serializer = OrderSerializer(self.order)

    def test_get_basket(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], self.serializer.data)

    def test_add_to_basket(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'id': self.order.id,
            'items': [
                {
                    'product_info': self.product_info.id,
                    'quantity': 2
                }
            ]
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(
            response.data['items'][0]['product_info'], self.product_info.id
        )
        self.assertEqual(response.data['items'][0]['quantity'], 2)

    def test_update_basket(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'id': self.order.id,
            'items': [
                {
                    'product_info': self.product_info.id,
                    'quantity': 3
                }
            ]
        }
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(
            response.data['items'][0]['product_info'], self.product_info.id
        )
        self.assertEqual(response.data['items'][0]['quantity'], 3)

    def test_delete_basket(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(user=self.user).exists())


class TestPartnerStatus(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass',
            type='shop'
        )
        self.shop = baker.make(Shop, user=self.user)
        self.url = reverse('partner-status')

    def test_get_shop_status(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ShopSerializer(self.shop).data)

    def test_update_shop_status_true(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={'status': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertEqual(self.shop.status, True)

    def test_update_shop_status_false(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={'status': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], False)
        self.assertEqual(self.shop.status, False)

    def test_update_shop_status_with_missing_argument(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestContactView(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = baker.make(User)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user-contact')

    def test_get_contacts(self):
        baker.make(Contact, user=self.user, _quantity=3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_create_contact_phone(self):
        data = {
            'type': 'phone',
            'value': '+1 123 456 7890'
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'phone')
        self.assertEqual(response.data['value'], '+1 123 456 7890')

    def test_update_contact(self):
        contact = baker.make(Contact, user=self.user)
        data = {
            'id': contact.id,
            'type': 'address',
            'value': 'Moscow, Mayakovsky st., 12a',
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'address')
        self.assertEqual(response.data['value'], 'Moscow, Mayakovsky st., 12a')
        contact.refresh_from_db()
        self.assertEqual(response.data['type'], contact.type)

    def test_delete_contact(self):
        contact = baker.make(Contact, user=self.user)
        data = {'id': contact.id}
        response = self.client.delete(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())


class TestOrderView(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass'
        )
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user,
        )
        self.url = reverse('order')

    def test_get_orders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order.id)

    def test_update_order(self):
        data = {'id': self.order.id}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'order updated'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'new')

    def test_update_order_not_found(self):
        data = {'id': self.order.id + 1}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data, {'error': 'order not found'}
        )

    def test_update_order_bad_request(self):
        data = {'id': 'not_an_integer'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {'error': 'bad request'}
        )


class ConfirmEmailViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.token = ConfirmEmailToken.objects.create(user=self.user)
        self.url = reverse('reg-user-confirm')

    def test_confirm_email_success(self):
        data = {'email': self.user.email, 'token': self.token.token}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(ConfirmEmailToken.objects.filter(token=self.token.token).exists())

    def test_confirm_email_token_not_found(self):
        data = {'email': self.user.email, 'token': 'invalidtoken'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(self.user.is_active)
        self.assertTrue(ConfirmEmailToken.objects.filter(token=self.token.token).exists())

    def test_confirm_email_missing_fields(self):
        data = {'email': self.user.email}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.is_active)
        self.assertTrue(ConfirmEmailToken.objects.filter(token=self.token.token).exists())


class PartnerUpdateTest(APITestCase):
    def setUp(self):
        # self.client = APIClient()
        self.client.defaults['CONTENT_TYPE'] = 'application/json'
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
            type='shop'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('partner-update')

    def test_partner_update_success_file(self):
        data = {
            'file': '/home/jerry/netology_hw/netology_dplm/data/shop_1.yaml'
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': True})

    def test_partner_update_bad_request(self):
        data = {
            'file': 'wrongtestfile'
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

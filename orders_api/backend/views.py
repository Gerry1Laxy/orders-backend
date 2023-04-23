from datetime import datetime
from distutils.util import strtobool
import yaml

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import QuerySet
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from backend.tasks import send_mail_task
from .permissions import IsShop

from .models import (
    ConfirmEmailToken,
    Contact,
    Order,
    ProductInfo,
    ProductParameter,
    Shop,
    Category,
    Product,
    Parameter
)
from .serializers import (
    CatygorySerializer,
    ContactSerializer,
    OrderSerializer,
    ProductInfoSerializer,
    ShopSerializer,
    UserSerializer
)


class RegisterUser(APIView):
    """
    This view registers a new user
    by accepting a POST request with the user's details.
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # password = make_password(serializer.validated_data['password'])
            # serializer.validated_data['password'] = password
            serializer.save()

            token, _ = ConfirmEmailToken.objects.get_or_create(
                user_id=serializer.data.get('id')
            )
            send_mail_task.delay(
                f'Confirm email for {token.user.username}',
                token.token,
                token.user.email
            )
            # register_new_user.send(
            #     sender=self.__class__,
            #     user_id=serializer.data.get('id')
            # )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


# class LoginUser(APIView):
#     def post(self, request):
#         username = request.data.get('username')
#         email = request.data.get('email')
#         password = request.data.get('password')
#         user = authenticate(username=username, email=email, password=password)
#         print(user)

#         if user:
#             token, created = Token.objects.get_or_create(user=user)
#             return Response({'token': token.key})
#         else:
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class LoginUser(APIView):
    """
    Authenticate a user with email and password,
    return a token to be used for further requests.
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if email is None or password is None:
            return Response({'error': 'Please provide both email and password'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)
        if user:
            print(user.password)

        if not user:
            return Response({'error': 'Invalid Credentials'},
                            status=status.HTTP_404_NOT_FOUND)

        # token = Token.objects.filter(user=user).first()
        # print(token)

        # if not token:
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key}, status=status.HTTP_200_OK)
    
    # def authenticate(self, email: str, password: str) -> User:
    #     user = User.objects.get(email=email)
    #     print(user)


class DetailUpdateUser(RetrieveUpdateAPIView):
    """
    This view is used for retrieving and updating a user's details.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class PartnerUpdate(APIView):
    """
    View to update a partner's shop with product information.
   
    Request Parameters:
    - YAML data containing information about the products to update. 
    """
    permission_classes = [IsAuthenticated, IsShop]
    
    # def post(self, request):
    #     return Response({'status': 'ok'})

    def post(self, request):
        # Load YAML data from request
        data, error = self.get_yaml_data(request)
        print(data)
        if data is None:
            return error

        # create or get the shop
        shop, _ = Shop.objects.get_or_create(
            name=data['shop'], user_id=request.user.id
        )

        # create or update categories
        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(
                id=category['id'], name=category['name']
            )
            category_object.shops.add(shop.id)
            category_object.save()

        # delete existing product info for the shop
        ProductInfo.objects.filter(shop_id=shop.id).delete()

        # create or update products and product info
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(
                name=item['name'], category_id=item['category']
            )

            product_info = ProductInfo.objects.create(
                product_id=product.id,
                external_id=item['id'],
                model=item['model'],
                price=item['price'],
                price_rrc=item['price_rrc'],
                quantity=item['quantity'],
                shop_id=shop.id
            )
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=value
                )

        return Response({'status': True}, status=status.HTTP_200_OK)

        # # Create or update Shop
        # shop_data = {'name': data.get('shop')}
        # shop_serializer = ShopSerializer(data=shop_data)
        # if shop_serializer.is_valid():
        #     shop, created = Shop.objects.update_or_create(name=shop_data['name'], defaults=shop_data)
        # else:
        #     return Response(shop_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # # Create or update Categories
        # category_serializer = CategorySerializer(data=data.get('categories'), many=True)
        # if category_serializer.is_valid():
        #     categories = category_serializer.save()
        # else:
        #     return Response(category_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # # Create or update Products
        # product_serializer = ProductSerializer(data=data.get('goods'), many=True)
        # if product_serializer.is_valid():
        #     for product_data in product_serializer.validated_data:
        #         product_data['shop'] = shop.id
        #         product_data['category'] = [category.id for category in categories if category.id == product_data['category']][0]
        #         Product.objects.update_or_create(id=product_data['id'], defaults=product_data)
        #     return Response({'message': 'Data updated successfully'}, status=status.HTTP_200_OK)
        # else:
        #     return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # return Response({'status': 'ok'})

    def get_yaml_data(self, request):
        url = request.data.get('url')
        file = request.data.get('file')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return None, Response(
                    {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )
            try:
                data = yaml.load(request.body, Loader=yaml.FullLoader)
            except yaml.YAMLError as e:
                return None, Response(
                    {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )
        if file:
            try:
                with open(file, 'r') as f:
                    data = yaml.safe_load(f)
            except FileNotFoundError as e:
                return None, Response(
                    {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )
        return data, None


class CategoryListView(ListAPIView):
    """
    API view that returns a list of all categories.
    """
    queryset = Category.objects.all()
    serializer_class = CatygorySerializer


# class ShopListView(ListAPIView):
#     """
#     API view that returns a list of all shops.
#     """
#     queryset = Shop.objects.all()
#     serializer_class = ShopSerializer


class ShopListRetrieveViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API viewset that provides list and retrieve actions for Shop model.
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ProductInfoListView(ListAPIView):
    """
    API view that returns a list of products
    with optional filtering, ordering, and searching.
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['shop_id', 'product__category_id']
    ordering_fields = ['price', 'quantity']
    search_fields = ['product__name', 'product__category__name']

    def get_queryset(self):
        queryset = ProductInfo.objects.all()
        queryset = self.filter_queryset(queryset)
        return queryset


class BasketView(APIView):
    """
    API view for managing the user's shopping basket.

    GET: Retrieves the items in the user's basket.
    POST: Adds an item to the user's basket.
    PUT: Updates an item in the user's basket.
    DELETE: Deletes the user's basket.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer

    def get(self, request):
        basket = Order.objects.filter(
            user=request.user, status='basket'
        ).all()
        if basket is None:
            return Response(
                {'error': 'basket not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(basket, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        basket = Order.objects.filter(user=request.user).first()
        if basket is None:
            return Response(
                {'error': 'basket not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(data=request.data, instance=basket)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        basket = Order.objects.filter(user=request.user).first()
        if basket is None:
            return Response(
                {'error': 'basket not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        basket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PartnerStatus(APIView):
    """
    API view to get or update the status of a shop.
    """
    permission_classes = (IsAuthenticated, IsShop)
    serializer_class = ShopSerializer

    def get(self, request):
        print(request.user.shop)
        serializer = self.serializer_class(request.user.shop)
        return Response(serializer.data)
    
    def post(self, request):
        status_shop = request.data.get('status')
        if status_shop:
            # request.user.shop.update(status=strtobool(status_shop))
            request.user.shop.status = strtobool(status_shop)
            serializer = self.serializer_class(request.user.shop)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'required arguments are missing'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PartnerOrderListView(ListAPIView):
    """
    API view that returns a list of orders that belong to the partner.
    """
    permission_classes = (IsAuthenticated, IsShop)
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(
            items__product_info__shop__user__id=self.request.user.id
        ).exclude(status='basket').distinct()
        return queryset


class ContactView(APIView):
    """
    API view for managing contacts associated with the authenticated user.

    GET: Returns a list of all contacts.
    POST: Creates a new contact.
    PUT: Updates an existing contact.
    DELETE: Deletes an existing contact.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ContactSerializer

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = self.serializer_class(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data.copy()
        contact = get_object_or_404(
            Contact, user=request.user, id=data.get('id')
        )
        serializer = self.serializer_class(
            contact, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        contact = get_object_or_404(
            Contact, user=request.user, id=request.data.get('id')
        )
        contact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderView(APIView):
    """
    API view for retrieving and updating orders belonging to the authenticated user.

    GET: Returns a list of orders associated with the authenticated user.
    POST: Updates the status of a specific order to "new".
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = Order.objects.filter(
            user=request.user
        )
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        order_id = request.data.get('id')
        if order_id:
            if type(order_id) == int:
                pass
            elif order_id.isdigit():
                order_id = int(order_id)
            else:
                return Response(
                    {'error': 'bad request'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order = Order.objects.filter(id=order_id)
            if order:
                is_update = order.update(status='new')
            else:
                return Response(
                    {'error': 'order not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if is_update:

                start = datetime.now()
                send_mail_task.delay(
                    'New status for order',
                    'Order status changed to new',
                    request.user.email
                )
                print(datetime.now() - start)
                # new_order.send(sender=self.__class__, user_id=request.user.id)
                return Response(
                    {'status': 'order updated'},
                    status=status.HTTP_200_OK
                )
        return Response(
            {'error': 'id field required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ConfirmEmailView(APIView):
    """
    View to confirm the email address of a user by validating a token.
    """
    
    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        if email and token:
            token_instance = ConfirmEmailToken.objects.filter(
                user__email=email,
                token=token
            ).first()
            if token_instance:
                token_instance.user.is_active = True
                token_instance.user.save()
                token_instance.delete()
                return Response(
                    {'status': 'success'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'token not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {'error': 'requered email and token'},
            status=status.HTTP_400_BAD_REQUEST
        )

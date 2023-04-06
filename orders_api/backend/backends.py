from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q

UserModel = get_user_model()

class EmailBackend(BaseBackend):
    def authenticate(self, requsts, email=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(Q(email=email))
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

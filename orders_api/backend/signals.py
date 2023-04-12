from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset import signals

from backend.models import ConfirmEmailToken, User


new_order = Signal(['user_id'])
register_new_user = Signal(['user_id'])


@receiver(signals.reset_password_token_created)
def reset_password_token_send_mail(
    sender,
    instanse,
    reset_password_token,
    **kwargs
):
    msg = EmailMultiAlternatives(
        f'Password reset Token for{reset_password_token.user}',
        reset_password_token.key,
        settings.SERVER_EMAIL,
        [reset_password_token.user.email]
    )
    msg.send()


@receiver(register_new_user)
def register_new_user_signal(user_id, **kwargs):
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        f'Confirm email for {token.user.username}',
        token.token,
        settings.SERVER_EMAIL,
        [token.user.email]
    )
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        'New status for order',
        'Order status changed to new',
        settings.SERVER_EMAIL,
        [user.email]
    )
    msg.send()

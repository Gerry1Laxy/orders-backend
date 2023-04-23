from django.dispatch import receiver
from django_rest_passwordreset import signals
from allauth.account.signals import user_signed_up

from backend.tasks import send_mail_task


@receiver(signals.reset_password_token_created)
def reset_password_token_send_mail(
    sender,
    instanse,
    reset_password_token,
    **kwargs
):
    '''
    Sends an email to the user containing the password reset token.
    '''
    send_mail_task.delay(
        f'Password reset Token for{reset_password_token.user}',
        reset_password_token.key,
        reset_password_token.user.email
    )


@receiver(user_signed_up)
def social_account_user_signup(request, user, **kwargs):
    '''
    The function sets the user's is_active to True
    if user signup with social accout (Yandex, ).
    '''
    if user.socialaccount_set.exists():
        user.is_active = True
        user.save()

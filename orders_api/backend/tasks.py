from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from celery import shared_task


@shared_task()
def send_mail_task(title: str, messege: str, email: str):
    '''
    Celery task that sends an email to User.
    '''
    msg = EmailMultiAlternatives(
        title,
        messege,
        settings.SERVER_EMAIL,
        [email]
    )
    msg.send()

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task
def send_welcome_email(user_id):
    from accounts.models import CustomUser

    user = CustomUser.objects.get(pk=user_id)
    html = render_to_string("emails/welcome.html", {"user": user})
    send_mail(
        subject="Welcome to NexusFlow",
        message=f"Hi {user.first_name}, welcome to NexusFlow.",
        from_email="noreply@nexusflow.io",
        recipient_list=[user.email],
        html_message=html,
        fail_silently=True,
    )

from celery import shared_task


@shared_task
def create_user_notification(recipient_id, message, link=""):
    from accounts.models import CustomUser
    from core.models import Notification

    try:
        recipient = CustomUser.objects.get(pk=recipient_id)
    except CustomUser.DoesNotExist:
        return

    Notification.objects.create(recipient=recipient, message=message, link=link or "")

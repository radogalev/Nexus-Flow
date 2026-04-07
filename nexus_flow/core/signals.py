from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Activity


@receiver(post_save)
def create_activity_for_project_and_task(sender, instance, created, **kwargs):
    sender_label = f"{sender._meta.app_label}.{sender.__name__}"

    if sender_label == "projects.Project" and created and instance.created_by:
        Activity.objects.create(
            actor=instance.created_by,
            verb="created project",
            content_object=instance,
        )

    if sender_label == "projects.Task" and instance.created_by:
        verb = "created task" if created else f"updated task status to {instance.status}"
        Activity.objects.create(
            actor=instance.created_by,
            verb=verb,
            content_object=instance,
        )

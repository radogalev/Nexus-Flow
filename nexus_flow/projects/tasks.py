from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task
def send_task_assignment_email(task_id):
    from projects.models import Task

    task = Task.objects.select_related("assigned_to", "project").get(pk=task_id)
    if not task.assigned_to:
        return

    html = render_to_string("emails/task_assigned.html", {"task": task})
    send_mail(
        subject=f"You have been assigned: {task.title}",
        message=f"You have a new task: {task.title} on project {task.project.title}.",
        from_email="noreply@nexusflow.io",
        recipient_list=[task.assigned_to.email],
        html_message=html,
        fail_silently=True,
    )

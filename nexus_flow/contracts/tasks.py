from celery import shared_task


@shared_task
def check_contract_expiry():
    from datetime import date, timedelta

    from contracts.models import Contract
    from core.models import Notification

    expiring = Contract.objects.filter(
        status="active",
        end_date__lte=date.today() + timedelta(days=14),
        end_date__gte=date.today(),
    ).select_related("company", "client")

    for contract in expiring:
        managers = contract.company.employees.filter(groups__name="Manager")
        for manager in managers:
            Notification.objects.get_or_create(
                recipient=manager,
                message=f'Contract "{contract.title}" expires in {contract.days_until_expiry} days.',
                defaults={"link": contract.get_absolute_url()},
            )


@shared_task
def send_project_deadline_reminder():
    from datetime import date, timedelta

    from projects.models import Project
    from core.models import Notification

    at_risk = Project.objects.filter(
        status="active",
        deadline__lte=date.today() + timedelta(days=7),
        deadline__gte=date.today(),
    ).select_related("created_by")

    for project in at_risk:
        if project.created_by and project.completion_percentage() < 50:
            Notification.objects.create(
                recipient=project.created_by,
                message=(
                    f'Project "{project.title}" is due in '
                    f'{(project.deadline - date.today()).days} days and is less than 50% complete.'
                ),
                link=project.get_absolute_url(),
            )

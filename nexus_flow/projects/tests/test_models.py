from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import CustomUser
from companies.models import Company
from projects.models import Project, Task


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="creator@test.com",
            password="StrongPass123!",
            first_name="Creator",
            last_name="User",
        )
        self.company = Company.objects.create(name="Acme", sector="tech", created_by=self.user)

    def create_project(self, **kwargs):
        defaults = {
            "title": "Project A",
            "company": self.company,
            "status": "active",
            "start_date": date.today() - timedelta(days=7),
            "deadline": date.today() + timedelta(days=7),
            "created_by": self.user,
        }
        defaults.update(kwargs)
        return Project.objects.create(**defaults)

    def test_project_is_overdue_past_deadline(self):
        project = self.create_project(deadline=date.today() - timedelta(days=1), status="active")
        self.assertTrue(project.is_overdue)

    def test_completion_percentage_no_tasks(self):
        project = self.create_project()
        self.assertEqual(project.completion_percentage(), 0)

    def test_completion_percentage_half_done(self):
        project = self.create_project()
        for idx in range(2):
            Task.objects.create(title=f"Done {idx}", project=project, status="done")
        for idx in range(2):
            Task.objects.create(title=f"Todo {idx}", project=project, status="todo")
        self.assertEqual(project.completion_percentage(), 50)

    def test_task_clean_due_date_before_start(self):
        project = self.create_project(start_date=date.today())
        task = Task(
            title="Invalid Task",
            project=project,
            due_date=date.today() - timedelta(days=1),
            status="todo",
        )
        with self.assertRaises(ValidationError):
            task.clean()

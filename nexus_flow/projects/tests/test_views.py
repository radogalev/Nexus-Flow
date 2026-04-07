from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from companies.models import Company
from projects.models import Project, Task


class ProjectsViewTests(TestCase):
    def setUp(self):
        self.manager_group, _ = Group.objects.get_or_create(name="Manager")
        self.employee_group, _ = Group.objects.get_or_create(name="Employee")

        self.manager = CustomUser.objects.create_user(
            email="manager@test.com",
            password="StrongPass123!",
            first_name="Manager",
            last_name="User",
        )
        self.manager.groups.add(self.manager_group)
        self.company = Company.objects.create(name="OrgCo", sector="tech", created_by=self.manager)
        self.manager.company = self.company
        self.manager.save()

        self.employee = CustomUser.objects.create_user(
            email="employee@test.com",
            password="StrongPass123!",
            first_name="Employee",
            last_name="User",
            company=self.company,
        )
        self.employee.groups.add(self.employee_group)

        self.other_user = CustomUser.objects.create_user(
            email="other@test.com",
            password="StrongPass123!",
            first_name="Other",
            last_name="User",
            company=self.company,
        )

        self.project_member = Project.objects.create(
            title="Member Project",
            company=self.company,
            status="active",
            start_date=date.today() - timedelta(days=2),
            deadline=date.today() + timedelta(days=10),
            created_by=self.manager,
        )
        self.project_member.members.add(self.employee)

        self.project_other = Project.objects.create(
            title="Other Project",
            company=self.company,
            status="active",
            start_date=date.today() - timedelta(days=2),
            deadline=date.today() + timedelta(days=10),
            created_by=self.manager,
        )

    def test_project_list_employee_sees_own_projects(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        qs = response.context["object_list"]
        self.assertIn(self.project_member, qs)
        self.assertNotIn(self.project_other, qs)

    def test_task_status_update_view_returns_json(self):
        task = Task.objects.create(
            title="Task",
            project=self.project_member,
            assigned_to=self.employee,
            created_by=self.manager,
            status="todo",
        )
        self.client.force_login(self.employee)
        response = self.client.post(
            reverse("projects:task_status_update"),
            {"task_id": task.id, "new_status": "in_progress"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "new_status": "in_progress"})

    def test_task_status_update_unauthorised_returns_403(self):
        task = Task.objects.create(
            title="Task",
            project=self.project_member,
            assigned_to=self.employee,
            created_by=self.manager,
            status="todo",
        )
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse("projects:task_status_update"),
            {"task_id": task.id, "new_status": "in_progress"},
        )
        self.assertEqual(response.status_code, 403)

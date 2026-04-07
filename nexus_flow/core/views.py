from datetime import date, datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.views.generic import ListView

from contracts.models import Client, Contract
from projects.models import Project, Task
from .models import Activity, Notification


def _is_manager(user):
	return user.is_superuser or user.groups.filter(name="Manager").exists()


class LandingView(TemplateView):
	template_name = "core/landing.html"

	def dispatch(self, request, *args, **kwargs):
		if request.user.is_authenticated:
			return redirect("core:dashboard")
		return super().dispatch(request, *args, **kwargs)


class DashboardView(TemplateView):
	template_name = "core/dashboard.html"

	def dispatch(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect("core:landing")
		return super().dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		today = date.today()
		now_hour = datetime.now().hour
		if now_hour < 12:
			context["day_greeting"] = "Good morning"
		elif now_hour < 18:
			context["day_greeting"] = "Good afternoon"
		else:
			context["day_greeting"] = "Good evening"

		assigned_tasks = user.assigned_tasks.select_related("project")
		context["my_tasks"] = assigned_tasks.exclude(status="done")[:10]
		context["task_stats"] = {
			"todo": assigned_tasks.filter(status="todo").count(),
			"in_progress": assigned_tasks.filter(status="in_progress").count(),
			"in_review": assigned_tasks.filter(status="in_review").count(),
			"done_this_week": assigned_tasks.filter(status="done", updated_at__gte=today - timedelta(days=7)).count(),
		}
		context["my_projects"] = user.projects.filter(status="active")[:5]

		if _is_manager(user) and user.company:
			context["expiring_contracts"] = Contract.objects.filter(
				company=user.company,
				status="active",
				end_date__lte=today + timedelta(days=30),
				end_date__gte=today,
			).order_by("end_date")
			context["company_overview"] = {
				"total_employees": user.company.employees.count(),
				"active_projects": user.company.projects.filter(status="active").count(),
			}
		else:
			context["expiring_contracts"] = Contract.objects.none()
			context["company_overview"] = None

		deadline_tasks = list(
			assigned_tasks.filter(
				Q(due_date__lte=today + timedelta(days=7)) & Q(due_date__isnull=False)
			).exclude(status="done")
		)

		if _is_manager(user) and user.company:
			project_scope = Project.objects.filter(company=user.company)
		else:
			project_scope = user.projects.all()

		deadline_projects = list(
			project_scope.filter(deadline__lte=today + timedelta(days=7)).exclude(status="completed")
		)

		upcoming_deadlines = []
		for task in deadline_tasks:
			remaining_days = (task.due_date - today).days
			upcoming_deadlines.append(
				{
					"type": "Task",
					"title": task.title,
					"url": task.get_absolute_url(),
					"due_date": task.due_date,
					"is_overdue": remaining_days < 0,
					"remaining_days": remaining_days,
				}
			)
		for project in deadline_projects:
			remaining_days = (project.deadline - today).days
			upcoming_deadlines.append(
				{
					"type": "Project",
					"title": project.title,
					"url": project.get_absolute_url(),
					"due_date": project.deadline,
					"is_overdue": remaining_days < 0,
					"remaining_days": remaining_days,
				}
			)

		context["upcoming_deadlines"] = sorted(upcoming_deadlines, key=lambda item: item["due_date"])[:8]
		context["today"] = today
		if user.company:
			context["recent_activity"] = Activity.objects.filter(actor__company=user.company).select_related("actor")[:10]
		else:
			context["recent_activity"] = Activity.objects.none()

		context["is_manager"] = _is_manager(user)
		return context


class SearchView(LoginRequiredMixin, TemplateView):
	template_name = "core/search.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		q = self.request.GET.get("q", "").strip()
		user = self.request.user
		is_manager = _is_manager(user)
		context["q"] = q
		results = {"projects": [], "tasks": [], "clients": [], "contracts": []}
		counts = {"projects": 0, "tasks": 0, "clients": 0, "contracts": 0}
		context["is_manager"] = is_manager
		context["total_results"] = 0

		if q:
			if user.is_superuser:
				project_qs = Project.objects.select_related("company")
				task_qs = Task.objects.select_related("project", "assigned_to")
				client_qs = Client.objects.select_related("company")
				contract_qs = Contract.objects.select_related("client")
			elif is_manager:
				project_qs = Project.objects.filter(company=user.company).select_related("company")
				task_qs = Task.objects.filter(project__company=user.company).select_related("project", "assigned_to")
				client_qs = Client.objects.filter(company=user.company).select_related("company")
				contract_qs = Contract.objects.filter(company=user.company).select_related("client")
			else:
				project_qs = Project.objects.filter(members=user).select_related("company")
				task_qs = Task.objects.filter(project__in=project_qs).select_related("project", "assigned_to")
				client_qs = Client.objects.none()
				contract_qs = Contract.objects.filter(projects__in=project_qs).select_related("client").distinct()

			results["projects"] = project_qs.filter(Q(title__icontains=q)).distinct()[:10]
			results["tasks"] = task_qs.filter(Q(title__icontains=q)).distinct()[:10]
			results["clients"] = client_qs.filter(Q(name__icontains=q)).distinct()[:10]
			results["contracts"] = contract_qs.filter(Q(title__icontains=q)).distinct()[:10]

			counts["projects"] = project_qs.filter(Q(title__icontains=q)).distinct().count()
			counts["tasks"] = task_qs.filter(Q(title__icontains=q)).distinct().count()
			counts["clients"] = client_qs.filter(Q(name__icontains=q)).distinct().count()
			counts["contracts"] = contract_qs.filter(Q(title__icontains=q)).distinct().count()
			context["total_results"] = sum(counts.values())

		context["results"] = results
		context["counts"] = counts
		return context


class NotificationListView(LoginRequiredMixin, ListView):
	model = Notification
	template_name = "core/notifications.html"
	paginate_by = 20

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["unread_count"] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
		return context


class NotificationMarkAllReadView(LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
		return redirect("core:notifications")


class NotificationOpenView(LoginRequiredMixin, View):
	def get(self, request, pk, *args, **kwargs):
		notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
		if not notification.is_read:
			notification.is_read = True
			notification.save(update_fields=["is_read"])
		if notification.link:
			return redirect(notification.link)
		return redirect("core:notifications")


class AboutView(TemplateView):
	template_name = "core/about.html"


class PrivacyView(TemplateView):
	template_name = "core/privacy.html"


def error_404(request, exception):
	return render(request, "errors/404.html", status=404)


def error_500(request):
	return render(request, "errors/500.html", status=500)

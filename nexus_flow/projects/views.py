from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.models import Activity
from core.tasks import create_user_notification
from .forms import ProjectCreateForm, ProjectEditForm, TaskCommentForm, TaskForm
from .models import Project, Task
from .tasks import send_task_assignment_email


def _is_manager(user):
	return user.is_superuser or user.groups.filter(name="Manager").exists()


class ProjectListView(LoginRequiredMixin, ListView):
	model = Project
	template_name = "projects/project_list.html"
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		if user.is_superuser:
			queryset = Project.objects.all()
		elif _is_manager(user):
			queryset = Project.objects.filter(company=user.company)
		else:
			queryset = Project.objects.filter(members=user)

		status = self.request.GET.get("status")
		if status:
			queryset = queryset.filter(status=status)

		sort = self.request.GET.get("sort")
		if sort in {"deadline", "-deadline", "created_at", "title"}:
			queryset = queryset.order_by(sort)
		else:
			queryset = queryset.order_by("-created_at")

		return queryset.annotate(task_count=Count("tasks")).distinct()


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
	model = Project
	slug_url_kwarg = "slug"
	template_name = "projects/project_detail.html"
	raise_exception = True

	def test_func(self):
		project = self.get_object()
		user = self.request.user
		if user.is_superuser:
			return True
		if _is_manager(user):
			return user.company_id == project.company_id
		return project.members.filter(pk=user.pk).exists()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		project = self.object
		context["todo_tasks"] = project.tasks.filter(status="todo")
		context["in_progress_tasks"] = project.tasks.filter(status="in_progress")
		context["in_review_tasks"] = project.tasks.filter(status="in_review")
		context["done_tasks"] = project.tasks.filter(status="done")
		context["members"] = project.members.all()
		context["recent_activity"] = Activity.objects.filter(content_type__model="task", object_id__in=project.tasks.values("id"))[:10]
		context["can_manage_project"] = self.request.user.is_superuser or (
			project.created_by_id == self.request.user.pk or (
				_is_manager(self.request.user) and self.request.user.company_id == project.company_id
			)
		)
		context["can_add_task"] = self.request.user.is_superuser or _is_manager(self.request.user) or project.members.filter(pk=self.request.user.pk).exists()
		context["can_delete_project"] = context["can_manage_project"]
		return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
	model = Project
	form_class = ProjectCreateForm
	template_name = "projects/project_form.html"

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["company"] = self.request.user.company
		return kwargs

	def form_valid(self, form):
		if not self.request.user.company_id and not self.request.user.is_superuser:
			return HttpResponseForbidden("You must belong to a company to create a project.")

		if not self.request.user.is_superuser:
			form.instance.company_id = self.request.user.company_id

		form.instance.created_by = self.request.user
		response = super().form_valid(form)
		member_ids = self.request.POST.getlist("members")
		if member_ids:
			valid_member_ids = self.object.company.employees.filter(pk__in=member_ids).values_list("pk", flat=True)
			self.object.members.set(valid_member_ids)
		self.object.members.add(self.request.user)
		return response


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Project
	form_class = ProjectEditForm
	slug_url_kwarg = "slug"
	template_name = "projects/project_form.html"

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return obj.created_by_id == self.request.user.pk or (
			_is_manager(self.request.user) and self.request.user.company_id == obj.company_id
		)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Project
	slug_url_kwarg = "slug"
	template_name = "projects/project_confirm_delete.html"
	success_url = reverse_lazy("projects:list")

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return obj.created_by_id == self.request.user.pk or (
			_is_manager(self.request.user) and self.request.user.company_id == obj.company_id
		)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["task_count"] = self.get_object().tasks.count()
		return context


class TaskDetailView(LoginRequiredMixin, DetailView):
	model = Task
	template_name = "projects/task_detail.html"

	def get_queryset(self):
		user = self.request.user
		queryset = Task.objects.select_related("project", "assigned_to")
		if user.is_superuser:
			return queryset
		if _is_manager(user):
			return queryset.filter(project__company_id=user.company_id)
		return queryset.filter(project__members=user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		task = self.object
		user = self.request.user
		is_manager = user.is_superuser or (_is_manager(user) and user.company_id == task.project.company_id)
		is_assignee = task.assigned_to_id == user.pk
		context["comment_form"] = TaskCommentForm()
		context["comments"] = task.comments.select_related("author")
		context["can_edit_task"] = is_manager or is_assignee
		context["can_delete_task"] = is_manager
		context["can_update_status"] = is_manager or is_assignee
		return context

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		form = TaskCommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.author = request.user
			comment.task = self.object
			comment.save()
		return redirect(self.object.get_absolute_url())


class TaskCreateView(LoginRequiredMixin, CreateView):
	model = Task
	form_class = TaskForm
	template_name = "projects/task_form.html"

	def get_project(self):
		return get_object_or_404(Project, slug=self.kwargs["project_slug"])

	def dispatch(self, request, *args, **kwargs):
		project = self.get_project()
		if not request.user.is_superuser and (
			(request.user not in project.members.all()) and not (
				_is_manager(request.user) and request.user.company_id == project.company_id
			)
		):
			return HttpResponseForbidden("You do not have permission to add tasks to this project.")
		return super().dispatch(request, *args, **kwargs)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["project"] = self.get_project()
		return kwargs

	def form_valid(self, form):
		project = self.get_project()
		form.instance.project = project
		form.instance.created_by = self.request.user
		response = super().form_valid(form)
		if self.object.assigned_to:
			send_task_assignment_email.delay(self.object.id)
			create_user_notification.delay(
				self.object.assigned_to_id,
				f"You have been assigned to task '{self.object.title}' on project '{project.title}'.",
				self.object.get_absolute_url(),
			)
		return response


class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Task
	form_class = TaskForm
	template_name = "projects/task_form.html"

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return obj.assigned_to_id == self.request.user.pk or (
			_is_manager(self.request.user) and self.request.user.company_id == obj.project.company_id
		)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["project"] = self.get_object().project
		return kwargs

	def form_valid(self, form):
		old_assignee = self.get_object().assigned_to
		response = super().form_valid(form)
		if old_assignee != self.object.assigned_to and self.object.assigned_to:
			send_task_assignment_email.delay(self.object.id)
			create_user_notification.delay(
				self.object.assigned_to_id,
				f"You have been assigned to task '{self.object.title}' on project '{self.object.project.title}'.",
				self.object.get_absolute_url(),
			)
		return response


class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Task
	template_name = "projects/task_confirm_delete.html"

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id == obj.project.company_id

	def get_success_url(self):
		return reverse("projects:detail", kwargs={"slug": self.object.project.slug})


class TaskStatusUpdateView(LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		task_id = request.POST.get("task_id")
		new_status = request.POST.get("new_status")
		task = get_object_or_404(Task, pk=task_id)

		valid_statuses = {choice[0] for choice in Task.STATUS_CHOICES}
		if new_status not in valid_statuses:
			return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

		is_manager = _is_manager(request.user) and request.user.company_id == task.project.company_id
		if not request.user.is_superuser and task.assigned_to != request.user and not is_manager:
			return JsonResponse({"success": False, "error": "Forbidden"}, status=403)

		task.status = new_status
		task.save(update_fields=["status", "updated_at"])
		Activity.objects.create(actor=request.user, verb=f"updated task status to {task.status}", content_object=task)
		return JsonResponse({"success": True, "new_status": task.status})

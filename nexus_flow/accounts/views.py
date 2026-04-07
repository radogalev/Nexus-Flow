from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
	LoginForm,
	PasswordChangeCustomForm,
	RegisterForm,
	UserProfileEditForm,
)
from .models import CustomUser
from .tasks import send_welcome_email


class RegisterView(CreateView):
	form_class = RegisterForm
	template_name = "accounts/register.html"
	success_url = reverse_lazy("accounts:login")

	def dispatch(self, request, *args, **kwargs):
		if request.user.is_authenticated:
			return redirect("core:dashboard")
		return super().dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		response = super().form_valid(form)
		user = self.object
		employee_group, _ = Group.objects.get_or_create(name="Employee")
		user.groups.add(employee_group)
		send_welcome_email.delay(user.id)
		messages.success(self.request, "Account created successfully. Please log in.")
		return response


class CustomLoginView(LoginView):
	form_class = LoginForm
	template_name = "accounts/login.html"
	redirect_authenticated_user = True


class CustomLogoutView(LoginRequiredMixin, View):
	http_method_names = ["post"]

	def post(self, request, *args, **kwargs):
		logout(request)
		return redirect("core:landing")


class PasswordHelpView(TemplateView):
	template_name = "accounts/password_help.html"


class UserProfileView(LoginRequiredMixin, DetailView):
	model = CustomUser
	template_name = "accounts/profile.html"
	context_object_name = "profile_user"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		profile_user = self.get_object()
		context["assigned_tasks"] = profile_user.assigned_tasks.select_related("project").order_by("status")[:10]
		return context


class UserProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = CustomUser
	form_class = UserProfileEditForm
	template_name = "accounts/profile_edit.html"

	def test_func(self):
		return self.request.user.pk == self.get_object().pk or self.request.user.is_superuser

	def get_success_url(self):
		return reverse("accounts:profile", kwargs={"pk": self.object.pk})


class PasswordChangeCustomView(LoginRequiredMixin, PasswordChangeView):
	form_class = PasswordChangeCustomForm
	template_name = "accounts/password_change.html"

	def get_success_url(self):
		return reverse("accounts:profile", kwargs={"pk": self.request.user.pk})


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
	permission_required = "accounts.view_customuser"
	model = CustomUser
	template_name = "accounts/user_list.html"

	def get_queryset(self):
		queryset = CustomUser.objects.filter(company=self.request.user.company)
		query = self.request.GET.get("q", "").strip()
		if query:
			queryset = queryset.filter(
				Q(first_name__icontains=query)
				| Q(last_name__icontains=query)
				| Q(email__icontains=query)
			)
		return queryset

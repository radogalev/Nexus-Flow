from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.models import CustomUser
from core.models import Activity
from .forms import CompanyCreateForm, CompanyEditForm, DepartmentDeleteConfirmForm, DepartmentForm
from .models import Company, Department


def _is_manager(user):
	return user.is_superuser or user.groups.filter(name="Manager").exists()


class CompanyListView(LoginRequiredMixin, ListView):
	model = Company
	template_name = "companies/company_list.html"
	paginate_by = 20

	def get_queryset(self):
		queryset = Company.objects.annotate(employee_count=Count("employees")).order_by("name")
		if self.request.user.is_superuser:
			return queryset
		if _is_manager(self.request.user) and self.request.user.company_id:
			return queryset.filter(pk=self.request.user.company_id)
		return queryset.filter(employees=self.request.user)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["can_create_company"] = _is_manager(self.request.user)
		return context


class CompanyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
	model = Company
	slug_url_kwarg = "slug"
	template_name = "companies/company_detail.html"
	raise_exception = True

	def test_func(self):
		company = self.get_object()
		user = self.request.user
		if user.is_superuser:
			return True
		if _is_manager(user):
			return user.company_id == company.pk
		return company.employees.filter(pk=user.pk).exists()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		company = self.object
		context["departments"] = company.departments.all()
		context["recent_activity"] = Activity.objects.filter(content_type__model="project", object_id__in=company.projects.values("id"))[:10]
		context["staff"] = company.employees.select_related("department").order_by("-date_joined")
		context["can_manage_company"] = _is_manager(self.request.user) and (
			self.request.user.is_superuser or self.request.user.company_id == company.pk
		)
		context["can_delete_company"] = self.request.user.is_superuser or company.created_by_id == self.request.user.pk
		return context


class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = Company
	form_class = CompanyCreateForm
	template_name = "companies/company_form.html"
	raise_exception = True

	def test_func(self):
		return _is_manager(self.request.user)

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Company
	form_class = CompanyEditForm
	slug_url_kwarg = "slug"
	template_name = "companies/company_form.html"

	def test_func(self):
		obj = self.get_object()
		return obj.created_by == self.request.user or self.request.user.is_superuser


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Company
	slug_url_kwarg = "slug"
	template_name = "companies/company_confirm_delete.html"
	success_url = reverse_lazy("companies:list")

	def test_func(self):
		obj = self.get_object()
		return obj.created_by == self.request.user or self.request.user.is_superuser

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		CustomUser.objects.filter(company=self.object).update(company=None, department=None)
		return super().delete(request, *args, **kwargs)


class DepartmentDetailView(LoginRequiredMixin, DetailView):
	model = Department
	template_name = "companies/department_detail.html"
	raise_exception = True

	def get_queryset(self):
		user = self.request.user
		queryset = Department.objects.select_related("company")
		if user.is_superuser:
			return queryset
		if user.company_id:
			return queryset.filter(company_id=user.company_id)
		return queryset.none()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["members"] = self.object.members.select_related("company").order_by("first_name", "last_name", "email")
		context["can_manage_department"] = _is_manager(self.request.user)
		return context


class DepartmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = Department
	form_class = DepartmentForm
	template_name = "companies/department_form.html"
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		if not _is_manager(self.request.user):
			return False
		company = get_object_or_404(Company, slug=self.kwargs["company_slug"])
		return self.request.user.company_id == company.pk

	def get_company(self):
		return get_object_or_404(Company, slug=self.kwargs["company_slug"])

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["company"] = self.get_company()
		return kwargs

	def form_valid(self, form):
		form.instance.company = self.get_company()
		return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Department
	form_class = DepartmentForm
	template_name = "companies/department_form.html"
	raise_exception = True

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id == obj.company_id

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["company"] = self.object.company
		return kwargs


class DepartmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Department
	template_name = "companies/department_confirm_delete.html"
	raise_exception = True

	def test_func(self):
		obj = self.get_object()
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id == obj.company_id

	def get_success_url(self):
		return reverse("companies:detail", kwargs={"slug": self.object.company.slug})

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		self.object.members.update(department=None)
		return super().delete(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		form = DepartmentDeleteConfirmForm(request.POST)
		if form.is_valid():
			return super().post(request, *args, **kwargs)
		context = self.get_context_data(form=form)
		return self.render_to_response(context)

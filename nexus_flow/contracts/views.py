from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ClientForm, ContractCreateForm, ContractEditForm, ContractServiceFormSet
from .models import Client, Contract, Service


def _is_manager(user):
	return user.is_superuser or user.groups.filter(name="Manager").exists()


def _build_service_formset(company, *args, **kwargs):
	formset = ContractServiceFormSet(*args, **kwargs)
	for form in formset.forms:
		form.fields["service"].queryset = Service.objects.filter(company=company)
	return formset


class ContractListView(LoginRequiredMixin, ListView):
	model = Contract
	template_name = "contracts/contract_list.html"
	paginate_by = 20

	def get_queryset(self):
		user = self.request.user
		if user.is_superuser:
			queryset = Contract.objects.all()
		elif _is_manager(user):
			queryset = Contract.objects.filter(company=user.company)
		else:
			queryset = Contract.objects.filter(company=user.company, projects__members=user).distinct()

		status = self.request.GET.get("status")
		if status:
			queryset = queryset.filter(status=status)
		return queryset

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["is_manager"] = _is_manager(self.request.user)
		if _is_manager(self.request.user):
			context["total_active_value"] = self.get_queryset().filter(status="active").aggregate(total=Sum("value"))["total"] or 0
		else:
			context["total_active_value"] = 0
		return context


class ContractDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
	model = Contract
	template_name = "contracts/contract_detail.html"
	raise_exception = True

	def test_func(self):
		contract = self.get_object()
		user = self.request.user
		if user.is_superuser:
			return True
		if _is_manager(user):
			return user.company_id == contract.company_id
		return contract.company_id == user.company_id and contract.projects.filter(members=user).exists()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		contract = self.object
		services = contract.contractservice_set.select_related("service")
		context["contract_services"] = services
		context["grand_total"] = sum(item.line_total for item in services)
		context["linked_projects"] = contract.projects.all()
		context["is_manager"] = _is_manager(self.request.user)
		return context


class ContractCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = Contract
	form_class = ContractCreateForm
	template_name = "contracts/contract_form.html"
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id is not None

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["company"] = self.request.user.company
		kwargs["user"] = self.request.user
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["formset"] = kwargs.get("formset") or _build_service_formset(self.request.user.company)
		return context

	def post(self, request, *args, **kwargs):
		self.object = None
		form = self.get_form()
		formset = _build_service_formset(self.request.user.company, self.request.POST)
		if form.is_valid() and formset.is_valid():
			contract = form.save(commit=False)
			contract.company = request.user.company
			contract.signed_by = request.user
			contract.status = "draft"
			contract.save()
			form.save_m2m()
			services = formset.save(commit=False)
			for item in services:
				item.contract = contract
				item.save()
			contract.recalculate_value()
			return redirect(contract.get_absolute_url())
		return self.render_to_response(self.get_context_data(form=form, formset=formset))


class ContractUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Contract
	form_class = ContractEditForm
	template_name = "contracts/contract_form.html"
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		if not _is_manager(self.request.user):
			return False
		return self.get_object().company_id == self.request.user.company_id

	def get_queryset(self):
		queryset = Contract.objects.all()
		if self.request.user.is_superuser:
			return queryset
		return queryset.filter(company_id=self.request.user.company_id)

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs["company"] = self.request.user.company
		kwargs["user"] = self.request.user
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["formset"] = kwargs.get("formset") or _build_service_formset(self.request.user.company, instance=self.object)
		return context

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		form = self.get_form()
		formset = _build_service_formset(self.request.user.company, self.request.POST, instance=self.object)
		if form.is_valid() and formset.is_valid():
			contract = form.save()
			formset.save()
			contract.recalculate_value()
			return redirect(contract.get_absolute_url())
		return self.render_to_response(self.get_context_data(form=form, formset=formset))


class ContractDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Contract
	template_name = "contracts/contract_confirm_delete.html"
	success_url = reverse_lazy("contracts:list")
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		if not _is_manager(self.request.user):
			return False
		return self.get_object().company_id == self.request.user.company_id

	def get_queryset(self):
		queryset = Contract.objects.all()
		if self.request.user.is_superuser:
			return queryset
		return queryset.filter(company_id=self.request.user.company_id)

	def delete(self, request, *args, **kwargs):
		contract = self.get_object()
		if contract.document:
			contract.document.delete(save=False)
		return super().delete(request, *args, **kwargs)


class ClientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
	model = Client
	template_name = "contracts/client_list.html"
	paginate_by = 20
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id is not None

	def get_queryset(self):
		if self.request.user.is_superuser:
			return Client.objects.all()
		return Client.objects.filter(company=self.request.user.company)


class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = Client
	form_class = ClientForm
	template_name = "contracts/client_form.html"
	success_url = reverse_lazy("contracts:client_list")
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id is not None

	def form_valid(self, form):
		form.instance.company = self.request.user.company
		return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Client
	form_class = ClientForm
	template_name = "contracts/client_form.html"
	success_url = reverse_lazy("contracts:client_list")
	raise_exception = True

	def test_func(self):
		if self.request.user.is_superuser:
			return True
		return _is_manager(self.request.user) and self.request.user.company_id is not None

	def get_queryset(self):
		if self.request.user.is_superuser:
			return Client.objects.all()
		return Client.objects.filter(company_id=self.request.user.company_id)


class ProtectedMediaView(LoginRequiredMixin, View):
	def get(self, request, filename, *args, **kwargs):
		contract = get_object_or_404(Contract, document=f"contract_docs/{filename}")
		if request.user.company != contract.company and not request.user.is_superuser:
			return HttpResponseForbidden("Forbidden")
		return FileResponse(contract.document.open("rb"))

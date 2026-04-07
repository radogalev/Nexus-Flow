from django.contrib import admin
from .models import Client, Contract, ContractService, Service


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ["name", "email", "company", "contact_person", "created_at"]
	list_filter = ["company", "created_at"]
	search_fields = ["name", "email", "contact_person"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
	list_display = ["name", "company", "unit_price"]
	list_filter = ["company"]
	search_fields = ["name", "company__name"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
	list_display = ["title", "client", "company", "status", "value", "end_date"]
	list_filter = ["status", "company"]
	search_fields = ["title", "client__name", "company__name"]


@admin.register(ContractService)
class ContractServiceAdmin(admin.ModelAdmin):
	list_display = ["contract", "service", "quantity"]
	search_fields = ["contract__title", "service__name"]

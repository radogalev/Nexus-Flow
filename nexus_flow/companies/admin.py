from django.contrib import admin
from .models import Company, Department


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
	list_display = ["name", "sector", "created_by", "created_at"]
	list_filter = ["sector", "created_at"]
	search_fields = ["name", "description", "website"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ["name", "company", "head", "created_at"]
	list_filter = ["company", "created_at"]
	search_fields = ["name", "company__name", "head__email"]

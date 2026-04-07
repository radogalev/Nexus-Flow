from django.urls import path

from . import views

app_name = "companies"

urlpatterns = [
	path("", views.CompanyListView.as_view(), name="list"),
	path("create/", views.CompanyCreateView.as_view(), name="create"),
	path("<slug:slug>/", views.CompanyDetailView.as_view(), name="detail"),
	path("<slug:slug>/edit/", views.CompanyUpdateView.as_view(), name="edit"),
	path("<slug:slug>/delete/", views.CompanyDeleteView.as_view(), name="delete"),
	path("<slug:company_slug>/departments/create/", views.DepartmentCreateView.as_view(), name="department_create"),
	path("departments/<int:pk>/", views.DepartmentDetailView.as_view(), name="department_detail"),
	path("departments/<int:pk>/edit/", views.DepartmentUpdateView.as_view(), name="department_edit"),
	path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),
]

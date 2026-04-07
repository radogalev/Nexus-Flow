from django.urls import path

from . import views

app_name = "contracts"

urlpatterns = [
	path("", views.ContractListView.as_view(), name="list"),
	path("create/", views.ContractCreateView.as_view(), name="create"),
	path("<int:pk>/", views.ContractDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.ContractUpdateView.as_view(), name="edit"),
	path("<int:pk>/delete/", views.ContractDeleteView.as_view(), name="delete"),
	path("clients/", views.ClientListView.as_view(), name="client_list"),
	path("clients/create/", views.ClientCreateView.as_view(), name="client_create"),
	path("clients/<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client_edit"),
	path("media/contract_docs/<str:filename>", views.ProtectedMediaView.as_view(), name="protected_media"),
]

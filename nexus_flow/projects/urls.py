from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
	path("", views.ProjectListView.as_view(), name="list"),
	path("create/", views.ProjectCreateView.as_view(), name="create"),
	path("<slug:slug>/", views.ProjectDetailView.as_view(), name="detail"),
	path("<slug:slug>/edit/", views.ProjectUpdateView.as_view(), name="edit"),
	path("<slug:slug>/delete/", views.ProjectDeleteView.as_view(), name="delete"),
	path("<slug:project_slug>/tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
	path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
	path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
	path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
	path("tasks/status/update/", views.TaskStatusUpdateView.as_view(), name="task_status_update"),
]

from django.contrib import admin
from .models import Project, ProjectMembership, Task, TaskComment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ["title", "company", "status", "start_date", "deadline"]
	list_filter = ["status", "company"]
	search_fields = ["title", "description", "company__name"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ["title", "project", "assigned_to", "status", "priority", "due_date"]
	list_filter = ["status", "priority", "project"]
	search_fields = ["title", "description", "project__title"]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
	list_display = ["task", "author", "created_at"]
	list_filter = ["created_at"]
	search_fields = ["body", "task__title", "author__email"]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
	list_display = ["project", "user", "added_at"]
	list_filter = ["added_at"]
	search_fields = ["project__title", "user__email"]

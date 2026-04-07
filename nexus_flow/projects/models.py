from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify

from datetime import date


class Project(models.Model):
	STATUS_CHOICES = [
		("planning", "Planning"),
		("active", "Active"),
		("on_hold", "On Hold"),
		("completed", "Completed"),
	]

	title = models.CharField(max_length=300)
	slug = models.SlugField(unique=True, blank=True)
	description = models.TextField(blank=True)
	company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="projects")
	members = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		through="ProjectMembership",
		related_name="projects",
		blank=True,
	)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")
	start_date = models.DateField()
	deadline = models.DateField()
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name="created_projects",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if not self.slug:
			self.slug = slugify(f"{self.title}-{self.id}")
			super().save(update_fields=["slug"])

	def clean(self):
		if self.deadline and self.start_date and self.deadline < self.start_date:
			raise ValidationError("Deadline must be after the start date.")

	@property
	def is_overdue(self):
		return self.deadline < date.today() and self.status != "completed"

	def completion_percentage(self):
		total_tasks = self.tasks.count()
		if total_tasks == 0:
			return 0
		done_tasks = self.tasks.filter(status="done").count()
		return int((done_tasks / total_tasks) * 100)

	def get_absolute_url(self):
		return reverse("projects:detail", kwargs={"slug": self.slug})

	def __str__(self):
		return self.title


class ProjectMembership(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	added_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = [["project", "user"]]


class Task(models.Model):
	STATUS_CHOICES = [
		("todo", "To Do"),
		("in_progress", "In Progress"),
		("in_review", "In Review"),
		("done", "Done"),
	]
	PRIORITY_CHOICES = [
		("low", "Low"),
		("medium", "Medium"),
		("high", "High"),
		("critical", "Critical"),
	]

	title = models.CharField(max_length=300)
	description = models.TextField(blank=True)
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
	assigned_to = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="assigned_tasks",
	)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name="created_tasks",
		editable=False,
	)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
	priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
	due_date = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["priority", "due_date"]

	def clean(self):
		if self.due_date and self.project and self.due_date < self.project.start_date:
			raise ValidationError("Due date cannot be before the project start date.")

	@property
	def is_overdue(self):
		return bool(self.due_date and self.due_date < date.today() and self.status != "done")

	def get_absolute_url(self):
		return reverse("projects:task_detail", kwargs={"project_slug": self.project.slug, "pk": self.pk})

	def __str__(self):
		return self.title


class TaskComment(models.Model):
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	body = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at"]

	def __str__(self):
		return self.body[:50]

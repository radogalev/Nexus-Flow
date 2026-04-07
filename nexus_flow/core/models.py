from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Activity(models.Model):
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
	verb = models.CharField(max_length=100)
	content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
	object_id = models.PositiveIntegerField(null=True)
	content_object = GenericForeignKey("content_type", "object_id")
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-timestamp"]
		verbose_name_plural = "activities"

	def __str__(self):
		return f"{self.actor} {self.verb}"


class Notification(models.Model):
	recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
	message = models.CharField(max_length=500)
	link = models.URLField(blank=True)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

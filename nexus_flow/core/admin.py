from django.contrib import admin
from .models import Activity, Notification


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
	list_display = ["actor", "verb", "timestamp"]
	list_filter = ["timestamp"]
	search_fields = ["actor__email", "verb"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ["recipient", "message", "is_read", "created_at"]
	list_filter = ["is_read", "created_at"]
	search_fields = ["recipient__email", "message"]

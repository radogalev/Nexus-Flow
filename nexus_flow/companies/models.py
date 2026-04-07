from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Company(models.Model):
	SECTOR_CHOICES = [
		("tech", "Technology"),
		("finance", "Finance"),
		("healthcare", "Healthcare"),
		("retail", "Retail"),
		("other", "Other"),
	]

	name = models.CharField(max_length=200, unique=True)
	slug = models.SlugField(unique=True, blank=True)
	sector = models.CharField(max_length=50, choices=SECTOR_CHOICES)
	description = models.TextField(blank=True)
	logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
	website = models.URLField(blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name="created_companies",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name_plural = "companies"
		ordering = ["name"]

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse("companies:detail", kwargs={"slug": self.slug})


class Department(models.Model):
	name = models.CharField(max_length=200)
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
	head = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="headed_departments",
	)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = [["name", "company"]]
		ordering = ["name"]

	def __str__(self):
		return f"{self.name} ({self.company.name})"

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse

from datetime import date
from decimal import Decimal


class Client(models.Model):
	name = models.CharField(max_length=200)
	email = models.EmailField()
	phone = models.CharField(max_length=20, blank=True)
	company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="clients")
	contact_person = models.CharField(max_length=200, blank=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class Service(models.Model):
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="services")

	def __str__(self):
		return f"{self.name} (${self.unit_price})"


class Contract(models.Model):
	STATUS_CHOICES = [
		("draft", "Draft"),
		("active", "Active"),
		("pending_renewal", "Pending Renewal"),
		("expired", "Expired"),
		("terminated", "Terminated"),
	]

	title = models.CharField(max_length=300)
	client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contracts")
	company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="contracts")
	services = models.ManyToManyField(Service, through="ContractService", related_name="contracts", blank=True)
	projects = models.ManyToManyField("projects.Project", related_name="contracts", blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
	value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	start_date = models.DateField()
	end_date = models.DateField()
	signed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name="signed_contracts",
	)
	notes = models.TextField(blank=True)
	document = models.FileField(upload_to="contract_docs/", blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def clean(self):
		if self.start_date and self.end_date and self.end_date <= self.start_date:
			raise ValidationError("End date must be after start date.")

	@property
	def days_until_expiry(self):
		return (self.end_date - date.today()).days

	@property
	def is_expiring_soon(self):
		days = self.days_until_expiry
		return 0 < days <= 30

	def recalculate_value(self):
		total = Decimal("0")
		for contract_service in self.contractservice_set.select_related("service").all():
			total += contract_service.line_total
		self.value = total
		self.save(update_fields=["value"])

	def get_absolute_url(self):
		return reverse("contracts:detail", kwargs={"pk": self.pk})

	def __str__(self):
		return self.title


class ContractService(models.Model):
	contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
	service = models.ForeignKey(Service, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)

	@property
	def line_total(self):
		return self.service.unit_price * self.quantity

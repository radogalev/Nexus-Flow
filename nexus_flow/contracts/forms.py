from django import forms
from django.forms import NumberInput, inlineformset_factory

from projects.models import Project
from .models import Client, Contract, ContractService


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email", "phone", "contact_person", "notes"]


class ContractCreateForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["title", "client", "start_date", "end_date", "projects", "notes", "document"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, company=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signed_by_display"] = forms.CharField(
            initial=user.full_name if user else "",
            disabled=True,
            required=False,
            label="Signed by",
        )
        if company is not None:
            self.fields["client"].queryset = Client.objects.filter(company=company)
            self.fields["projects"].queryset = Project.objects.filter(company=company)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after the start date.")
        return cleaned_data


class ContractEditForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["title", "client", "status", "start_date", "end_date", "projects", "notes", "document"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, company=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signed_by_display"] = forms.CharField(
            initial=user.full_name if user else "",
            disabled=True,
            required=False,
            label="Signed by",
        )
        if company is not None:
            self.fields["client"].queryset = Client.objects.filter(company=company)
            self.fields["projects"].queryset = Project.objects.filter(company=company)


ContractServiceFormSet = inlineformset_factory(
    Contract,
    ContractService,
    fields=["service", "quantity"],
    extra=1,
    can_delete=True,
    widgets={"quantity": NumberInput(attrs={"min": 1})},
)

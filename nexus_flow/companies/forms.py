from django import forms
from django.core.exceptions import ValidationError

from accounts.models import CustomUser
from .models import Company, Department


class CompanyCreateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "sector", "description", "logo", "website"]
        help_texts = {
            "name": "The official registered name of your company.",
        }
        widgets = {
            "website": forms.URLInput(attrs={"placeholder": "https://yourcompany.com"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise ValidationError("Company name cannot be empty.")
        return name


class CompanyEditForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "sector", "description", "logo", "website"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        created_by_name = ""
        if self.instance and self.instance.created_by:
            created_by_name = self.instance.created_by.full_name
        self.fields["created_by_display"] = forms.CharField(
            initial=created_by_name,
            disabled=True,
            required=False,
            label="Created by",
        )


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "head", "description"]

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["head"].queryset = CustomUser.objects.filter(company=company)


class DepartmentDeleteConfirmForm(forms.Form):
    confirm = forms.CharField(widget=forms.TextInput, label='Type "DELETE" to confirm')

    def clean_confirm(self):
        value = self.cleaned_data["confirm"]
        if value != "DELETE":
            raise ValidationError('You must type "DELETE" exactly to confirm.')
        return value

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import CustomUser
from .models import Project, Task, TaskComment


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description", "company", "status", "start_date", "deadline"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["company"].initial = company
            self.fields["company"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        deadline = cleaned_data.get("deadline")
        if start_date and deadline and deadline < start_date:
            raise ValidationError("Deadline must be after the start date.")
        return cleaned_data


class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description", "company", "status", "start_date", "deadline"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

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


class ProjectMemberForm(forms.Form):
    members = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["members"].queryset = project.company.employees.all()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "priority", "status", "due_date"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["assigned_to"].queryset = project.members.all()

        if self.instance and self.instance.pk:
            creator = self.instance.created_by.full_name if self.instance.created_by else "-"
            self.fields["created_by_display"] = forms.CharField(
                initial=creator,
                disabled=True,
                required=False,
                label="Created by",
            )


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["body"]
        labels = {"body": "Your comment"}
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a comment..."}),
        }

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
import re

from .models import CustomUser


class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "job_title", "password1", "password2"]
        labels = {
            "email": "Email address",
            "first_name": "First name",
            "last_name": "Last name",
            "job_title": "Job title",
            "password1": "Password",
            "password2": "Confirm password",
        }
        help_texts = {
            "email": "You will use this to log in.",
            "job_title": "Your current role or position.",
            "password1": "At least 8 characters, including at least one number.",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "your@email.com"}),
            "job_title": forms.TextInput(attrs={"placeholder": "e.g. Software Engineer"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and not re.search(r"\d", password):
            raise ValidationError("This password must contain at least one number.")
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields did not match.")
        return password2


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autofocus": True, "placeholder": "your@email.com"}),
    )
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    error_messages = {
        "invalid_login": "Please enter a correct email and password. Note that both fields are case-sensitive.",
        "inactive": "This account is inactive.",
    }


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone_number", "job_title", "bio", "avatar"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "avatar-input"}),
        }


class PasswordChangeCustomForm(PasswordChangeForm):
    old_password = forms.CharField(label="Current password", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm new password", widget=forms.PasswordInput)


class UserDepartmentAssignForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["department", "company"]

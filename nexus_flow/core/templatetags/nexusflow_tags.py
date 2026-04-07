from datetime import date

from django import template
from django.db.models import Sum

from contracts.models import Contract
from core.models import Notification

register = template.Library()


@register.filter(name="days_remaining")
def days_remaining(value):
    if not value:
        return 0
    return (value - date.today()).days


@register.filter(name="is_overdue")
def is_overdue(value):
    if not value:
        return False
    return value < date.today()


@register.filter(name="status_badge_class")
def status_badge_class(value):
    mapping = {
        "active": "success",
        "draft": "secondary",
        "expired": "danger",
        "planning": "info",
        "completed": "success",
        "on_hold": "warning",
    }
    return mapping.get(value, "secondary")


@register.simple_tag(name="unread_notifications", takes_context=True)
def unread_notifications(context):
    user = context.get("request").user
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, is_read=False).count()


@register.simple_tag(name="sum_active_contracts")
def sum_active_contracts(company):
    return Contract.objects.filter(company=company, status="active").aggregate(t=Sum("value"))["t"] or 0

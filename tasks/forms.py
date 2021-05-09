from django import forms
from tasks.models import Task


class TaskCreationForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "team",
            "base_points_prize",
            "refresh_interval",
            "is_recurring",
        ]

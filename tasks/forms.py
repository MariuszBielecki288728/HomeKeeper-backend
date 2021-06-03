from django import forms
from tasks.models import Task, TaskInstanceCompletion


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


class TaskInstanceCompletionForm(forms.ModelForm):
    class Meta:
        model = TaskInstanceCompletion
        fields = ["task_instance"]

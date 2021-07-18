from django import forms
from tasks.models import TaskInstanceCompletion


class TaskInstanceCompletionForm(forms.ModelForm):
    class Meta:
        model = TaskInstanceCompletion
        fields = ["task_instance"]

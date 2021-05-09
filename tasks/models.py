from django.conf import settings
from django.db import models
from teams.models import Team
from common.models import TrackingFieldsMixin

from django.core.validators import MinValueValidator


class Task(TrackingFieldsMixin):
    """Data model representing task, includes description of the task."""

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    base_points_prize = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    refresh_interval = models.DurationField()
    is_recurring = models.BooleanField()


class TaskInstance(TrackingFieldsMixin):
    """
    Data model representing instance of a task, includes reference to the task.
    Since tasks may be reoccuring, this model is a representation of a single occurence.
    """

    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    active_from = models.DateTimeField()

    def calculate_prize(self):
        return self.task.base_points_prize


class TaskInstanceCompletion(TrackingFieldsMixin):
    """
    Data model that represents the event of user completing the task.
    """

    task_instance = models.ForeignKey(TaskInstance, on_delete=models.PROTECT)
    user_who_completed_task = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )

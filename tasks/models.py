import datetime
import math
import typing

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now


from teams.models import Team
from common.models import TrackingFieldsMixin

POINTS_INCREASE_INTERVAL = 7


class Task(TrackingFieldsMixin):
    """Data model representing task, includes description of the task."""

    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)

    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    base_points_prize = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    refresh_interval = models.DurationField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)

    @property
    def active(self) -> bool:
        """
        The Task is active when:
            it is not deleted
            and there is at least one task instance that is active.
        """
        return super().active and any(
            ti.active
            for ti in TaskInstance.objects.filter(
                task=self.id,
            ).all()
        )


class TaskInstance(TrackingFieldsMixin):
    """
    Data model representing instance of a task, includes reference to the task.
    Since tasks may be reoccuring, this model is a representation of a single occurence.
    """

    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    active_from = models.DateTimeField()
    completed = models.BooleanField(default=False)

    @property
    def active(self) -> bool:
        """
        The TaskInstance is active when:
            it is not deleted
            and is not completed
            and the current date is after the active_from field value
            and the task it is related to is not deleted.

        TODO: Add tests for these calculations
        """
        return (
            self.completed is False
            and self.active_from <= now()
            and super().active
            and self.task.deleted_at is None
        )

    @property
    def current_prize(self) -> int:
        """Calculates current value of the points reward for task instance completion.

        In order to encourage users to complete stale tasks, the current prize
        increase over time. For recurring tasks, base points prize is multiplied
        by the number of times that interval has passed twice. For single tasks,
        the constant is taken as interval - currently 7 days.
        """
        multiplication_interval = self.task.refresh_interval or datetime.timedelta(
            days=POINTS_INCREASE_INTERVAL
        )
        return self.task.base_points_prize * math.ceil(
            (now() - self.active_from) / (multiplication_interval * 2)
        )


class TaskInstanceCompletion(TrackingFieldsMixin):
    """
    Data model that represents the event of user completing the task.
    """

    task_instance = models.ForeignKey(TaskInstance, on_delete=models.PROTECT)
    user_who_completed_task = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    points_granted = models.IntegerField()

    def save(self, *args, **kwargs):
        if self._state.adding is True:
            self.grant_points_prize()
        super().save(*args, **kwargs)

    def grant_points_prize(self):
        """
        Sets current reward of the task as granted points. Does not save.
        """
        self.points_granted = self.task_instance.current_prize

    @staticmethod
    def count_user_points(
        user_id: int,
        team_id: int,
        from_datetime: typing.Optional[datetime.datetime] = None,
        to_datetime: typing.Optional[datetime.datetime] = None,
    ) -> int:
        """
        Counts points for a given user in a given team.
        User has to be a member of the given team.
        There may be datetime bounds specified (inclusive).

        Note:
            Consider making it a user or member ("through" model) method.
        """
        query = TaskInstanceCompletion.objects.filter(
            user_who_completed_task=user_id,
            task_instance__task__team=team_id,
            deleted_at=None,
            task_instance__deleted_at=None,
            task_instance__task__deleted_at=None,
        )
        if from_datetime is not None:
            query = query.filter(created_at__gte=from_datetime)
        if to_datetime is not None:
            query = query.filter(created_at__lte=to_datetime)

        return (
            query.distinct().aggregate(models.Sum("points_granted"))[
                "points_granted__sum"
            ]
            or 0
        )

from django.db import models
from teams.models import Team
from common.models import TrackingFieldsMixin

from django.core.validators import MinValueValidator


class Task(TrackingFieldsMixin):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    base_points_prize = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    refresh_interval = models.DurationField()
    is_reoccuring = models.BooleanField()

from django.db import models
from django.conf import settings
from common.models import TrackingFieldsMixin


class Team(TrackingFieldsMixin):
    name = models.CharField(max_length=50)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)

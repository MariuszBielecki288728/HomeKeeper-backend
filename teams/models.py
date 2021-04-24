from django.db import models
from django.conf import settings
from common.models import TrackingFieldsMixin
from django.contrib.auth import hashers


class TeamManager(models.Manager):
    def create_team(self, name: str, password: str):
        if not name:
            raise ValueError("Team must have a name")
        if not password:
            raise ValueError("Team must have a password")

        team = self.model(name=name)
        team.set_password(password)
        team.save()
        return team


class Team(TrackingFieldsMixin):
    name = models.CharField(max_length=50)
    # TODO
    # https://docs.djangoproject.com/en/3.2/topics/db/models/#extra-fields-on-many-to-many-relationships
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)
    password = models.CharField(
        max_length=50, help_text="Password used to join the team"
    )
    objects = TeamManager()

    def set_password(self, raw_password: str) -> None:
        """
        Sets the team's password to the given raw string,
        taking care of the password hashing. Doesn’t save the Team object.
        """
        password = hashers.make_password(raw_password)
        self.password = password

    def check_password(self, raw_password: str) -> bool:
        """
        Returns True if the given raw string is the correct password for the user.
        """
        return hashers.check_password(raw_password, self.password)

from django.db import models
from django.conf import settings
from common.models import TrackingFieldsMixin
from django.contrib.auth import hashers
from django.core.validators import MinLengthValidator


class TeamManager(models.Manager):
    def create_team(self, name: str, password: str, **kwargs):
        if not name:
            raise ValueError("Team must have a name")
        if not password:
            raise ValueError("Team must have a password")

        team = self.model(name=name, **kwargs)
        team.set_password(password)
        team.save()
        return team


class Team(TrackingFieldsMixin):
    name = models.CharField(max_length=50, validators=[MinLengthValidator(1)])
    # TODO
    # https://docs.djangoproject.com/en/3.2/topics/db/models/#extra-fields-on-many-to-many-relationships
    members = models.ManyToManyField(settings.AUTH_USER_MODEL)
    password = models.CharField(
        max_length=128, help_text="Password used to join the team"
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

    @staticmethod
    def check_membership(user_id: int, team_id: int) -> None:
        team = Team.objects.get(pk=team_id)
        if not team.members.filter(id=user_id).exists():
            raise ValueError(f"User {user_id} is not a member of team {team_id}")

    @staticmethod
    def check_users_in_the_same_team(user_id: int, other_user_id: int) -> None:
        if (
            not Team.objects.filter(members__id=user_id)
            .filter(members__id=other_user_id)
            .exists()
        ):
            raise ValueError(
                f"User {user_id} is not in the same team as {other_user_id}"
            )

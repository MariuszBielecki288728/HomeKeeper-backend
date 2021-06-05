from django.test import TestCase
from django.contrib.auth import get_user_model

from teams.models import Team


class TeamTestCase(TestCase):
    def test_manager_create_team_helper(self):
        password = "pswd"
        t = Team.objects.create_team("TeamAmebki", password)
        self.assertTrue(t.check_password(password))
        self.assertFalse(t.check_password("not a password"))
        self.assertNotEqual(password, t.password)

    def test_manager_create_team_invalid_input(self):
        self.assertRaises(ValueError, Team.objects.create_team, "", "pswd")
        self.assertRaises(ValueError, Team.objects.create_team, "name", "")

    def test_check_membership(self):
        user = get_user_model().objects.create(username="John")
        team = Team.objects.create(name="John's team")
        with self.assertRaisesRegex(
            ValueError, f"User {user.id} is not a member of team {team.id}"
        ):
            Team.check_membership(user, team.id)
        team.members.add(user)
        Team.check_membership(user, team.id)

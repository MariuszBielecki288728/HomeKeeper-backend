from django.test import TestCase

from common.tests import factories
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
        user = factories.UserFactory()
        team = factories.TeamFactory()
        with self.assertRaisesRegex(
            ValueError, f"User {user.id} is not a member of team {team.id}"
        ):
            Team.check_membership(user.id, team.id)
        team.members.add(user)
        Team.check_membership(user.id, team.id)

    def test_users_in_the_same_team(self):
        [user, other_user] = factories.UserFactory.create_batch(2)
        team = factories.TeamFactory()

        with self.assertRaisesRegex(
            ValueError, f"User {user.id} is not in the same team as {other_user.id}"
        ):
            Team.check_users_in_the_same_team(user.id, other_user.id)

        team.members.add(user)
        with self.assertRaisesRegex(
            ValueError, f"User {user.id} is not in the same team as {other_user.id}"
        ):
            Team.check_users_in_the_same_team(user.id, other_user.id)

        team.members.add(other_user)
        Team.check_users_in_the_same_team(user.id, other_user.id)

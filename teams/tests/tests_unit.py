from django.test import TestCase
from teams.models import Team


class AnimalTestCase(TestCase):
    def test_manager_create_team_helper(self):
        password = "pswd"
        t = Team.objects.create_team("TeamAmebki", password)
        self.assertTrue(t.check_password(password))
        self.assertFalse(t.check_password("not a password"))
        self.assertNotEqual(password, t.password)

    def test_manager_create_team_invalid_input(self):
        self.assertRaises(ValueError, Team.objects.create_team, "", "pswd")
        self.assertRaises(ValueError, Team.objects.create_team, "name", "")
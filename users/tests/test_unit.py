from django.test import TestCase

from common.tests import factories

from users.models import Profile


class UserUnitTestCase(TestCase):
    def test_profile_signal(self):
        user = factories.UserFactory()
        profs = list(Profile.objects.filter(user=user).all())
        self.assertEqual(len(profs), 1)
        self.assertEqual(user.profile, profs[0])
        self.assertIsNone(profs[0].image_id)

    def test_profile_factory(self):
        user = factories.UserFactoryNoSignals()
        profs = list(Profile.objects.filter(user=user).all())
        self.assertEqual(len(profs), 1)
        self.assertIsNotNone(profs[0].image_id)

    def test_profile_signal_changes_are_visible(self):
        some_text = "abc"

        user = factories.UserFactory()
        user.profile.image_id = some_text
        user.profile.save()
        prof = Profile.objects.get(user=user)
        self.assertEqual(user.profile.image_id, some_text)
        self.assertEqual(prof.image_id, some_text)

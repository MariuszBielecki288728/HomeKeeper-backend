from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth.models import User
from graphql_jwt.testcases import JSONWebTokenTestCase

from common.tests import factories
from .queries import REGISTER_MUTATION


class UserAuthTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "johnpassword"
        )
        self.client.authenticate(self.user)

    def test_auth_me(self):
        query = """
            query {
                me {
                    id
                    username
                }
            }
            """

        response = self.client.execute(query)
        self.assertIsNone(response.errors)
        response.data["me"]["username"] == "john"

    def test_register(self):
        query = REGISTER_MUTATION.format(
            username="Agatka", password="nieszczycielskiehaslo", email="puci@puci.puci"
        )
        response = self.client.execute(query)
        assert len(response.data["register"]["errors"]) == 0
        assert response.data["register"]["username"] == "Agatka"

    def test_register_is_validated(self):
        query = REGISTER_MUTATION.format(
            username="Agatka", password="weak", email="puci@puci.puci"
        )
        response = self.client.execute(query)
        assert (
            "This password is too short"
            in response.data["register"]["errors"][0]["messages"][0]
        )


class UserProfileTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = factories.UserFactoryNoSignals()
        self.client.authenticate(self.user)

    def test_my_profile(self):
        query = """
            query {
                me {
                    username
                    profile {
                        imageId
                        colorId
                    }
                }
            }
            """

        response = self.client.execute(query)
        self.assertIsNone(response.errors)
        self.assertEqual(response.data["me"]["username"], self.user.username)
        self.assertEqual(
            response.data["me"]["profile"]["imageId"], self.user.profile.image_id
        )
        self.assertEqual(
            response.data["me"]["profile"]["colorId"], self.user.profile.color_id
        )

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth.models import User
from graphql_jwt.testcases import JSONWebTokenTestCase

from .queries import REGISTER_MUTATION


class UserTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "john", "lennon@thebeatles.com", "johnpassword"
        )
        self.client.authenticate(self.user)

    def test_users(self):
        query = """
            query {
                users {
                    id
                    username
                }
            }
        """

        response = self.client.execute(query)

        assert not response.errors

        assert len(response.data["users"]) == 1
        assert response.data["users"][0]["username"] == "john"

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

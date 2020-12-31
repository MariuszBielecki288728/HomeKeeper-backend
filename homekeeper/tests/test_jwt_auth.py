import json

from django.test import TestCase
from django.contrib.auth.models import User


class JWTTestCase(TestCase):
    def setUp(self):
        self.user_name = "john"
        self.user_password = "johnpassword"
        self.user = User.objects.create_user(
            self.user_name, "lennon@thebeatles.com", self.user_password
        )

    def test_jwt_auth(self):
        response = self.client.post(
            path="/graphql/",
            data={
                "query": (
                    "mutation {"
                    f'tokenAuth(username: "{self.user_name}", password: "{self.user_password}") {{'
                    "token } }"
                )
            },
        )
        response_content = json.loads(response.content.decode("utf-8"))
        token = response_content["data"]["tokenAuth"]["token"]

        response = self.client.post(
            path="/graphql/",
            data={"query": "query { me { username } }"},
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        response_content = json.loads(response.content.decode("utf-8"))
        assert response_content["data"]["me"]["username"] == "john"

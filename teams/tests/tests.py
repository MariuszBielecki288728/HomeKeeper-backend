from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase
import unittest


class TeamTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "john", "lennon@thebeatles.com", "johnpassworddfasdf"
        )
        self.client.authenticate(self.user)

    # @unittest.SkipTest
    def test_create_team(self):
        team_name = "Puciciele"
        query = self.query(
            f"""
            mutation {{
                createTeam (input: {{
                    name: "{team_name}"
                }}){{
                    team {{
                    id
                    createdBy {{
                        username
                    }}
                    name
                    }}
                }}
            }}
            """
        )

        response = self.client.execute(query)
        assert response.data["createTeam"]["team"]["name"] == team_name
        assert response.data["createTeam"]["team"]["createdBy"]["username"] == "john"

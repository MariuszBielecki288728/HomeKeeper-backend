from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.testcases import JSONWebTokenTestCase

from teams.models import Team
from common.tests.factories import TeamFactory, UserFactory


class TeamTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.member = UserFactory()
        self.client.authenticate(self.user)

        self.team = TeamFactory(
            name="Amebki", created_by=self.user, members=[self.member]
        )

        for i in range(5):
            t = Team(name=str(i))
            t.save()

    def test_create_team(self):
        team_name = "Puciciele"
        password = "passwd"

        query = f"""
            mutation {{
                createTeam (input: {{
                    name: "{team_name}",
                    password: "{password}"
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

        response = self.client.execute(query)
        assert response.data["createTeam"]["team"]["name"] == team_name
        assert (
            response.data["createTeam"]["team"]["createdBy"]["username"]
            == self.user.username
        )
        t = Team.objects.get(name=team_name)
        assert t.check_password(password)
        assert not t.check_password("not_a_password")
        assert self.user in t.members.all()

    def test_teams(self):

        query = """
            query {
                teams {
                    id
                    name
                    members {
                    username
                    }
                }
            }
            """
        response = self.client.execute(query)
        assert len(response.data["teams"]) == 6

    def test_my_team(self):
        query = """
            query {
                myTeams {
                    name
                }
            }
            """
        response = self.client.execute(query)
        assert response.data["myTeams"][0]["name"] == "Amebki"

    def test_team_members_default(self):
        query = """
            query {
                teamMembers {
                    username
                }
            }
            """
        response = self.client.execute(query)
        self.assertEqual(
            response.data["teamMembers"][0]["username"], self.user.username
        )
        self.assertEqual(
            response.data["teamMembers"][1]["username"], self.member.username
        )

    def test_team_members_by_team_id(self):
        team = TeamFactory(created_by=self.user)

        query = f"""
            query {{
                teamMembers (teamId: {team.id}) {{
                    username
                }}
            }}
            """
        response = self.client.execute(query)
        self.assertEqual(
            response.data["teamMembers"][0]["username"], self.user.username
        )
        self.assertEqual(len(response.data["teamMembers"]), 1)

    def test_team_members_by_wrong_team_id(self):
        team = TeamFactory()

        query = f"""
            query {{
                teamMembers (teamId: {team.id}) {{
                    username
                }}
            }}
            """
        response = self.client.execute(query)
        self.assertEqual(
            response.errors[0].message,
            "You are not a member of the team or the given team does not exist.",
        )

    def test_team_join(self):
        team = TeamFactory()
        password = "passwd"
        team.set_password(password)
        team.save()
        query = f"""
        mutation {{
            joinTeam (teamId: {team.id}, password: "{password}") {{
                team {{
                    id
                    name
                    members {{
                        username
                    }}
                }}
            }}
        }}
        """
        response = self.client.execute(query)
        self.assertEqual(response.data["joinTeam"]["team"]["name"], team.name)
        assert self.user in team.members.all()

    def test_team_join_invalid_password(self):
        team = TeamFactory()
        team.set_password("passwd")
        team.save()
        query = f"""
        mutation {{
            joinTeam (teamId: {team.id}, password: "not_a_password") {{
                team {{
                    id
                    name
                    members {{
                        username
                    }}
                }}
            }}
        }}
        """
        response = self.client.execute(query)
        assert response.errors
        self.assertEqual(response.errors[0].message, f"Wrong password for {team.name}")
        assert self.user not in team.members.all()

    def test_team_leave(self):
        query = f"""
        mutation {{
            leaveTeam (teamId: {self.team.id}) {{
                team {{
                    id
                    name
                    members {{
                        username
                    }}
                }}
            }}
        }}
        """
        response = self.client.execute(query)
        assert response.data["leaveTeam"]["team"]["name"] == "Amebki"
        assert self.user not in self.team.members.all()

    def test_team_leave_without_argument(self):
        """John should leave random team"""
        query = """
        mutation {
            leaveTeam {
                team {
                    id
                    name
                    members {
                        username
                    }
                }
            }
        }
        """
        response = self.client.execute(query)
        team = Team.objects.get(pk=response.data["leaveTeam"]["team"]["id"])
        assert self.user not in team.members.all()

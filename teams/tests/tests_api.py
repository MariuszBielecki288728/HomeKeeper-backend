from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase

from teams.models import Team


class TeamTestCase(GraphQLTestCase, JSONWebTokenTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "john", "lennon@thebeatles.com", "johnpassworddfasdf"
        )
        self.member = get_user_model().objects.create_user(
            "Dan", "dd@ggl.com", "danpasswd"
        )
        self.client.authenticate(self.user)

        self.team = Team(name="Amebki")
        self.team.save()
        self.team.members.add(self.user)
        self.team.members.add(self.member)

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
        assert response.data["createTeam"]["team"]["createdBy"]["username"] == "john"
        t = Team.objects.get(name=team_name)
        assert t.check_password(password)
        assert not t.check_password("not_a_password")

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
        self.assertEqual(response.data["teamMembers"][0]["username"], "john")
        self.assertEqual(response.data["teamMembers"][1]["username"], "Dan")

    def test_team_members_by_team_id(self):
        team = Team.objects.create_team("TeamSingle", "pass")
        team.members.add(self.user)
        team.save()

        query = f"""
            query {{
                teamMembers (teamId: {team.id}) {{
                    username
                }}
            }}
            """
        response = self.client.execute(query)
        self.assertEqual(response.data["teamMembers"][0]["username"], "john")
        self.assertEqual(len(response.data["teamMembers"]), 1)

    def test_team_members_by_wrong_team_id(self):
        team = Team.objects.create_team("TeamEmpty", "pass")

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
        team = Team(name="Test")
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
        assert response.data["joinTeam"]["team"]["name"] == "Test"
        assert self.user in team.members.all()

    def test_team_join_invalid_password(self):
        team = Team(name="Test")
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
        assert response.errors[0].message == "Wrong password for Test"
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

import datetime
import pytz
from parameterized import parameterized
from unittest import mock

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase

from teams.models import Team
from tasks.models import TaskInstance, Task


def create_task_query(name, team_id, base_prize=10):
    return f"""
        mutation {{
            createTask (input: {{
                name: "{name}",
                team: "{team_id}"
                basePointsPrize: {str(base_prize)}
            }}) {{
                errors {{
                field
                messages
                }}
                task {{
                    id
                    createdAt
                    createdBy {{
                        username
                    }}
                    modifiedAt
                    deletedAt
                    name
                    description
                    team {{
                        id
                        name
                        members {{
                        username
                        }}
                        taskSet {{
                        id
                        name
                        }}
                    }}
                refreshInterval
                isRecurring
                }}
            }}
        }}
        """


class TaskTestCase(GraphQLTestCase, JSONWebTokenTestCase):
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

        self.tasks = [
            Task(name="1", team=self.team, base_points_prize=10),
            Task(name="2", team=self.team, base_points_prize=10),
            Task(name="3", team=self.team, base_points_prize=10),
        ]
        for t in self.tasks:
            t.save()

    def test_create_task(self):
        name = "Clean the bathroom"
        team_id = self.team.id
        query = create_task_query(name, team_id)
        mocked = datetime.datetime(2018, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertFalse(response.data["createTask"]["errors"])
        self.assertEqual(name, response.data["createTask"]["task"]["name"])
        self.assertEqual(
            self.team.id, int(response.data["createTask"]["task"]["team"]["id"])
        )
        task_instance = TaskInstance.objects.filter(
            task_id=response.data["createTask"]["task"]["id"]
        ).first()

        self.assertEqual(task_instance.active_from, mocked)

    def test_create_task_wrong_team(self):
        name = "Clean the bathroom"

        team = Team(name="SomeOtherTeam")
        team.save()

        team_id = team.id
        query = create_task_query(name, team_id)
        response = self.client.execute(query)

        assert len(response.errors)
        self.assertEqual(
            response.errors[0].message,
            "Only members of the given team may create tasks",
        )

    @parameterized.expand(["true", "false"])
    def test_tasks_query(self, only_active):
        query = f"""query {{
            tasks(teamId: {self.team.id}, onlyActive: {only_active}){{
                id
                name
                description
                team {{
                    id
                    name
                }}
            }}
        }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertEqual(len(response.data["tasks"]), 3)
        self.assertEqual(response.data["tasks"][1]["name"], self.tasks[1].name)
        self.assertEqual(
            response.data["tasks"][1]["team"]["id"], str(self.tasks[1].team.id)
        )

    def test_task_instances_query(self):
        query = f"""query {{
            taskInstances(teamId: {self.team.id}) {{
                id
                task {{
                    name
                    team {{
                        id
                    }}
                }}
            }}
        }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertEqual(len(response.data["taskInstances"]), 3)
        self.assertEqual(
            response.data["taskInstances"][1]["task"]["name"], self.tasks[1].name
        )
        self.assertEqual(
            response.data["taskInstances"][1]["task"]["team"]["id"],
            str(self.tasks[1].team.id),
        )

    def test_related_task_instances(self):
        query = f"""query {{
            relatedTaskInstances(taskId: {self.tasks[2].id}) {{
                id
                task {{
                    name
                    team {{
                        id
                    }}
                }}
            }}
        }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertEqual(len(response.data["relatedTaskInstances"]), 1)
        self.assertEqual(
            response.data["relatedTaskInstances"][0]["task"]["name"], self.tasks[2].name
        )
        self.assertEqual(
            response.data["relatedTaskInstances"][0]["task"]["team"]["id"],
            str(self.tasks[2].team.id),
        )
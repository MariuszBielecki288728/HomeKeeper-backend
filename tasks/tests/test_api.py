import datetime
import pytz
from parameterized import parameterized
from unittest import mock

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase

from teams.models import Team
from tasks.models import TaskInstance, Task


def create_task_query(name, team_id, base_prize=10, interval=None):
    return f"""
        mutation {{
            createTask (input: {{
                name: "{name}"
                team: "{team_id}"
                basePointsPrize: {str(base_prize)}
                {"isRecurring: true" if interval else ""}
                {f'refreshInterval: "{interval}"' if interval else ""}
            }}) {{
                errors {{
                field
                messages
                }}
                task {{
                    id
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

    def test_create_task_with_interval(self):
        name = "Clean the bathroom"
        team_id = self.team.id
        query = create_task_query(name, team_id, interval="P7D")
        mocked = datetime.datetime(2018, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertFalse(response.data["createTask"]["errors"])
        self.assertEqual(name, response.data["createTask"]["task"]["name"])
        self.assertEqual(
            self.team.id, int(response.data["createTask"]["task"]["team"]["id"])
        )
        self.assertEqual(
            "7 days, 0:00:00", response.data["createTask"]["task"]["refreshInterval"]
        )
        self.assertTrue(response.data["createTask"]["task"]["isRecurring"])
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

    @parameterized.expand(["true", "false"])
    def test_task_instances_query(self, only_active):
        query = f"""query {{
            taskInstances(teamId: {self.team.id}, onlyActive: {only_active}) {{
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

    @parameterized.expand(["true", "false"])
    def test_related_task_instances(self, only_active):
        query = f"""query {{
            relatedTaskInstances(taskId: {self.tasks[2].id}, onlyActive: {only_active}) {{
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

    def test_submit_completion(self):
        task_instances = TaskInstance.objects.filter(task=self.tasks[0])
        self.assertEqual(len(list(task_instances.all())), 1)
        task_instance = task_instances.first()
        query = f""" mutation {{submitTaskInstanceCompletion(input: {{taskInstance: {task_instance.id}}}) {{
            errors {{
            field
            messages
            }}
            taskInstanceCompletion {{
            userWhoCompletedTask {{
                id
                username
            }}
            taskInstance {{id, task {{id, name}}, activeFrom, completed, active}}
            }}
        }} }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertFalse(response.data["submitTaskInstanceCompletion"]["errors"])
        self.assertEqual(
            response.data["submitTaskInstanceCompletion"]["taskInstanceCompletion"][
                "userWhoCompletedTask"
            ]["id"],
            str(self.user.id),
        )
        self.assertEqual(
            response.data["submitTaskInstanceCompletion"]["taskInstanceCompletion"][
                "taskInstance"
            ]["id"],
            str(task_instance.id),
        )
        task_instances = TaskInstance.objects.filter(
            task=self.tasks[0], completed=False
        )
        self.assertEqual(len(list(task_instances.all())), 0)
        self.assertFalse(self.tasks[0].active)
        self.assertTrue(self.tasks[1].active)

    def test_submit_completion_on_recurring_task(self):
        refresh_interval = datetime.timedelta(days=14)
        task = Task.objects.create(
            name="Umyć podłogę",
            team=self.team,
            base_points_prize=5,
            is_recurring=True,
            refresh_interval=refresh_interval,
        )
        task_instance = TaskInstance.objects.filter(task=task).first()
        query = f""" mutation {{submitTaskInstanceCompletion(input: {{taskInstance: {task_instance.id}}}) {{
            errors {{
                field
                messages
            }}
            taskInstanceCompletion {{
            userWhoCompletedTask {{
                id
                username
            }}
            taskInstance {{id, task {{id, name}}, activeFrom, completed, active}}
            }}
        }} }}"""
        mocked = datetime.datetime(2018, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertFalse(response.data["submitTaskInstanceCompletion"]["errors"])
        self.assertEqual(
            response.data["submitTaskInstanceCompletion"]["taskInstanceCompletion"][
                "userWhoCompletedTask"
            ]["id"],
            str(self.user.id),
        )
        self.assertEqual(
            response.data["submitTaskInstanceCompletion"]["taskInstanceCompletion"][
                "taskInstance"
            ]["id"],
            str(task_instance.id),
        )
        task_instances = TaskInstance.objects.filter(task=task)
        self.assertEqual(len(list(task_instances.all())), 2)
        active_instance = task_instances.filter(completed=False).first()
        self.assertTrue(active_instance.active)
        self.assertEqual(mocked + refresh_interval, active_instance.active_from)

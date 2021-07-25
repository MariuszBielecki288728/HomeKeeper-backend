import datetime
import pytz
from parameterized import parameterized
from unittest import mock

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase

from common.tests import factories

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
                {f'refreshInterval: {interval}' if interval else ""}
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
        query = create_task_query(name, team_id, interval=604800)
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

    def test_update_task(self):
        task = factories.TaskFactory()
        base_prize = task.base_points_prize + 5
        old_desc = task.description
        query = f"""
        mutation {{
            updateTask (input: {{
                id: {task.id}
                basePointsPrize: {base_prize}
            }}) {{
                errors {{
                field
                messages
                }}
                task {{
                    id
                    name
                    description
                    basePointsPrize
                    team {{
                        id
                    }}
                refreshInterval
                isRecurring
                }}
            }}
        }}
        """
        response = self.client.execute(query)
        task.refresh_from_db()
        assert not response.errors
        assert not response.data["updateTask"]["errors"]
        self.assertEqual(
            base_prize, response.data["updateTask"]["task"]["basePointsPrize"]
        )
        self.assertEqual(base_prize, task.base_points_prize)
        self.assertEqual(base_prize, task.base_points_prize)
        self.assertEqual(old_desc, response.data["updateTask"]["task"]["description"])

    def test_delete_task(self):
        task = factories.TaskFactory()
        old_desc = task.description
        self.assertTrue(task.active)
        query = f"""
        mutation {{
            deleteTask (id: {task.id}) {{
                errors {{
                field
                messages
                }}
                task {{
                    id
                    name
                    description
                    basePointsPrize
                    team {{
                        id
                    }}
                refreshInterval
                isRecurring
                }}
            }}
        }}
        """
        mocked = datetime.datetime(2018, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            response = self.client.execute(query)
        task.refresh_from_db()
        assert not response.errors
        assert not response.data["deleteTask"]["errors"]
        self.assertEqual(str(task.id), response.data["deleteTask"]["task"]["id"])
        self.assertEqual(old_desc, task.description)
        self.assertFalse(task.active)
        self.assertEqual(mocked, task.deleted_at)

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

    def test_revert_completion(self):
        completion = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.member, task_instance__task__team=self.team
        )
        task = completion.task_instance.task

        task_instances = TaskInstance.objects.filter(task=task)
        self.assertEqual(len(list(task_instances.all())), 1)

        query = f""" mutation {{revertTaskInstanceCompletion(id: {completion.id}) {{
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
        self.assertFalse(response.data["revertTaskInstanceCompletion"]["errors"])
        self.assertEqual(
            response.data["revertTaskInstanceCompletion"]["taskInstanceCompletion"][
                "userWhoCompletedTask"
            ]["id"],
            str(self.member.id),
        )
        self.assertEqual(
            response.data["revertTaskInstanceCompletion"]["taskInstanceCompletion"][
                "taskInstance"
            ]["id"],
            str(completion.task_instance.id),
        )
        completion.task_instance.refresh_from_db()
        task.refresh_from_db()
        task_instances = TaskInstance.objects.filter(task=task)
        self.assertEqual(len(list(task_instances.all())), 1)
        self.assertTrue(task.active)
        self.assertIsNone(completion.task_instance.deleted_at)

    def test_user_points(self):
        completions = factories.TaskInstanceCompletionFactory.create_batch(
            10,
            user_who_completed_task=self.user,
            task_instance__task__team=self.team,
        )
        query = f"""query {{
            userPoints(userId: {self.user.id}, teamId: {self.team.id})
        }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertEqual(
            response.data["userPoints"],
            sum(comp.points_granted for comp in completions),
        )

    def test_user_points_with_datetime(self):
        query = f"""query {{
            userPoints(
                userId: {self.user.id},
                teamId: {self.team.id},
                fromDatetime: "2013-07-16T19:23"
            )
        }}"""

        with mock.patch(
            "tasks.models.TaskInstanceCompletion.count_user_points",
            mock.Mock(return_value=0),
        ) as mocked:
            response = self.client.execute(query)
            mocked.assert_called_with(
                self.user.id,
                self.team.id,
                datetime.datetime(2013, 7, 16, 19, 23),
                None,
            )
        self.assertFalse(response.errors)
        self.assertEqual(
            response.data["userPoints"],
            0,
        )

    def test_team_members_points(self):
        user_completions = factories.TaskInstanceCompletionFactory.create_batch(
            10,
            user_who_completed_task=self.user,
            task_instance__task__team=self.team,
        )
        member_completions = factories.TaskInstanceCompletionFactory.create_batch(
            5,
            user_who_completed_task=self.member,
            task_instance__task__team=self.team,
        )
        query = f"""query {{
            teamMembersPoints(teamId: {self.team.id}) {{
                member {{
                    username
                }}
                points
            }}
        }}"""
        response = self.client.execute(query)
        self.assertFalse(response.errors)
        self.assertEqual(
            response.data["teamMembersPoints"][0]["member"]["username"],
            self.user.username,
        )
        self.assertEqual(
            response.data["teamMembersPoints"][0]["points"],
            sum(comp.points_granted for comp in user_completions),
        )
        self.assertEqual(
            response.data["teamMembersPoints"][1]["member"]["username"],
            self.member.username,
        )
        self.assertEqual(
            response.data["teamMembersPoints"][1]["points"],
            sum(comp.points_granted for comp in member_completions),
        )

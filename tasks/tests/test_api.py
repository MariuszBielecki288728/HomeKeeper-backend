import datetime
import pytz
from unittest import mock

from graphene_django.utils.testing import GraphQLTestCase
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase

from teams.models import Team
from tasks.models import TaskInstance


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

    def test_create_task(self):
        name = "Clean the bathroom"
        team_id = self.team.id
        query = f"""
            mutation {{
                createTask (input: {{
                    name: "{name}",
                    team: "{team_id}"
                    basePointsPrize: 10
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

import datetime
import pytz

from parameterized import parameterized
from unittest import mock
from django.test import TestCase

from common.tests import factories
from tasks.models import TaskInstanceCompletion


class TaskPrizeUnitTestCase(TestCase):
    def setUp(self):
        active_from = datetime.datetime(2018, 4, 2, 0, 0, 0, tzinfo=pytz.utc)
        task = factories.TaskFactoryNoSignals(
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=1),
        )
        self.task_instance = factories.TaskInstanceFactory(
            task=task, active_from=active_from
        )

    @parameterized.expand(
        [
            (datetime.datetime(2018, 4, 2, 1, 0, 0, tzinfo=pytz.utc), 1),
            (datetime.datetime(2018, 4, 3, 1, 0, 0, tzinfo=pytz.utc), 1),
            (datetime.datetime(2018, 4, 3, 23, 0, 0, tzinfo=pytz.utc), 1),
            (datetime.datetime(2018, 4, 4, 1, 0, 0, tzinfo=pytz.utc), 2),
            (datetime.datetime(2018, 4, 5, 0, 0, 0, tzinfo=pytz.utc), 2),
            (datetime.datetime(2018, 4, 5, 22, 0, 0, tzinfo=pytz.utc), 2),
            (datetime.datetime(2018, 4, 6, 1, 0, 0, tzinfo=pytz.utc), 3),
            (datetime.datetime(2018, 4, 7, 1, 0, 0, tzinfo=pytz.utc), 3),
            (datetime.datetime(2018, 4, 8, 1, 0, 0, tzinfo=pytz.utc), 4),
        ]
    )
    def test_points_calculating_n_interval_passed(self, now, mult):
        with mock.patch("tasks.models.now", mock.Mock(return_value=now)):
            self.assertEqual(
                self.task_instance.current_prize,
                self.task_instance.task.base_points_prize * mult,
            )


class TaskUnitPrizeBiggerIntervalTestCase(TestCase):
    def setUp(self):
        active_from = datetime.datetime(2018, 4, 2, 0, 0, 0, tzinfo=pytz.utc)
        task = factories.TaskFactoryNoSignals(
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=30),
            base_points_prize=15,
        )
        self.task_instance = factories.TaskInstanceFactory(
            task=task, active_from=active_from
        )

    @parameterized.expand(
        [
            (datetime.datetime(2018, 4, 2, 1, 0, 0, tzinfo=pytz.utc), 1),
            (datetime.datetime(2018, 5, 3, 1, 0, 0, tzinfo=pytz.utc), 1),
            (datetime.datetime(2018, 6, 16, 1, 0, 0, tzinfo=pytz.utc), 2),
            (datetime.datetime(2018, 8, 5, 0, 0, 0, tzinfo=pytz.utc), 3),
            (datetime.datetime(2018, 11, 8, 1, 0, 0, tzinfo=pytz.utc), 4),
        ]
    )
    def test_points_calculating_n_big_interval_passed(self, now, mult):
        with mock.patch("tasks.models.now", mock.Mock(return_value=now)):
            self.assertEqual(
                self.task_instance.current_prize,
                self.task_instance.task.base_points_prize * mult,
            )


class TaskInstanceCompletionUserPointsTestCase(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        self.other_user_with_no_completions = factories.UserFactory()
        self.team = factories.TeamFactory(
            members=[self.user, self.other_user_with_no_completions]
        )
        self.completions = factories.TaskInstanceCompletionFactory.create_batch(
            10,
            user_who_completed_task=self.user,
            task_instance__task__team=self.team,
        )
        self.points_sum = sum(comp.points_granted for comp in self.completions)
        self.some_completions_of_other_users = (
            factories.TaskInstanceCompletionFactory.create_batch(5)
        )

    def test_simple(self):
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(self.user.id, self.team.id),
            self.points_sum,
        )

    def test_no_points(self):
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(
                self.other_user_with_no_completions.id, self.team.id
            ),
            0,
        )

    def test_date_from(self):
        some_date_before = datetime.datetime(2020, 4, 3, 0, 0, 0, tzinfo=pytz.utc)
        from_date = datetime.datetime(2020, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        some_date_after = datetime.datetime(2020, 4, 10, 0, 0, 0, tzinfo=pytz.utc)

        comp_before_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        # TODO created_at ignores values from factory, should be improved
        comp_before_date.created_at = some_date_before
        comp_before_date.save()

        comp_after_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_after_date.created_at = some_date_after
        comp_after_date.save()

        self.assertEqual(
            TaskInstanceCompletion.count_user_points(
                self.other_user_with_no_completions.id,
                self.team.id,
                from_datetime=from_date,
            ),
            comp_after_date.points_granted,
        )

    def test_date_to(self):
        some_date_before = datetime.datetime(2020, 4, 3, 0, 0, 0, tzinfo=pytz.utc)
        to_date = datetime.datetime(2020, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        some_date_after = datetime.datetime(2020, 4, 10, 0, 0, 0, tzinfo=pytz.utc)

        comp_before_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_before_date.created_at = some_date_before
        comp_before_date.save()

        comp_after_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_after_date.created_at = some_date_after
        comp_after_date.save()

        self.assertEqual(
            TaskInstanceCompletion.count_user_points(
                self.other_user_with_no_completions.id,
                self.team.id,
                to_datetime=to_date,
            ),
            comp_before_date.points_granted,
        )

    def test_date_from_to(self):
        some_date_before = datetime.datetime(2020, 4, 3, 0, 0, 0, tzinfo=pytz.utc)
        from_date = datetime.datetime(2020, 4, 4, 0, 0, 0, tzinfo=pytz.utc)
        to_date = datetime.datetime(2020, 4, 6, 0, 0, 0, tzinfo=pytz.utc)
        ok_date = datetime.datetime(2020, 4, 5, 0, 0, 0, tzinfo=pytz.utc)
        some_date_after = datetime.datetime(2020, 4, 10, 0, 0, 0, tzinfo=pytz.utc)

        comp_before_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_before_date.created_at = some_date_before
        comp_before_date.save()

        comp_after_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_after_date.created_at = some_date_after
        comp_after_date.save()

        comp_ok_date = factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
        )
        comp_ok_date.created_at = ok_date
        comp_ok_date.save()

        self.assertEqual(
            TaskInstanceCompletion.count_user_points(
                self.other_user_with_no_completions.id,
                self.team.id,
                from_datetime=from_date,
                to_datetime=to_date,
            ),
            comp_ok_date.points_granted,
        )

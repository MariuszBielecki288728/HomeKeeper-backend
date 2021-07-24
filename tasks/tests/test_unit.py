import datetime
import pytz

from parameterized import parameterized
from unittest import mock
from django.test import TestCase
from django.utils import timezone

from common.tests import factories

from tasks.models import TaskInstance, TaskInstanceCompletion


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

        factories.TaskInstanceCompletionFactory(
            user_who_completed_task=self.other_user_with_no_completions,
            task_instance__task__team=self.team,
            created_at=some_date_before,
        )

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


class TaskInstanceCompletionSignalsTestCase(TestCase):
    def setUp(self) -> None:
        self.member = factories.UserFactory()
        self.team = factories.TeamFactory(members=[self.member])

    def test_revert_single_task(self):
        task_instance = factories.TaskInstanceFactory(task__team=self.team)
        completion = factories.TaskInstanceCompletionFactory(
            task_instance=task_instance, user_who_completed_task=self.member
        )
        task_instance.refresh_from_db()
        self.assertTrue(task_instance.completed)
        self.assertEqual(
            TaskInstance.objects.filter(task=task_instance.task).count(), 1
        )
        self.assertFalse(task_instance.active)
        self.assertFalse(task_instance.task.active)

        now = timezone.now()
        with mock.patch("common.models.timezone.now", mock.Mock(return_value=now)):
            completion.delete()
        completion.refresh_from_db()
        task_instance.refresh_from_db()

        self.assertEqual(completion.deleted_at, now)
        self.assertFalse(completion.active)
        self.assertTrue(task_instance.active)
        self.assertEqual(
            TaskInstance.objects.filter(task=task_instance.task).count(), 1
        )
        self.assertTrue(task_instance.task.active)

    def test_revert_reccurrent_task(self):
        task = factories.TaskFactoryNoSignals(
            team=self.team,
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=5),
        )
        task_instance = factories.TaskInstanceFactory(
            task=task, active_from=task.created_at
        )
        with mock.patch(
            "tasks.models.now",
            mock.Mock(return_value=task.created_at + datetime.timedelta(days=2)),
        ):
            completion = factories.TaskInstanceCompletionFactory(
                task_instance=task_instance, user_who_completed_task=self.member
            )
        task_instance.refresh_from_db()
        self.assertEqual(
            completion.points_granted, task_instance.task.base_points_prize
        )
        self.assertTrue(task_instance.completed)
        self.assertIsNone(task_instance.deleted_at)
        self.assertEqual(TaskInstance.objects.filter(task=task).count(), 2)
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(self.member.id, self.team.id),
            completion.points_granted,
        )

        now = task.created_at + datetime.timedelta(days=4)
        with mock.patch("common.models.timezone.now", mock.Mock(return_value=now)):
            completion.delete()

        task_instance.refresh_from_db()
        self.assertTrue(task_instance.completed)
        with mock.patch(
            "tasks.models.now", mock.Mock(return_value=now + datetime.timedelta(days=2))
        ):
            self.assertFalse(task_instance.active)

        self.assertEqual(task_instance.deleted_at, now)
        self.assertEqual(TaskInstance.objects.filter(task=task).count(), 2)
        self.assertEqual(
            TaskInstance.objects.filter(
                task=task, completed=False, deleted_at=None
            ).count(),
            1,
        )
        new_task_instance = TaskInstance.objects.filter(
            task=task, completed=False, deleted_at=None
        ).first()
        with mock.patch(
            "tasks.models.now", mock.Mock(return_value=now + datetime.timedelta(days=2))
        ):
            self.assertTrue(new_task_instance.active)
        self.assertEqual(new_task_instance.active_from, task_instance.active_from)
        self.assertEqual(new_task_instance.active_from, task.created_at)
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(self.member.id, self.team.id), 0
        )

    def test_revert_reccurrent_task_but_it_was_completed_since_then(self):
        task = factories.TaskFactoryNoSignals(
            team=self.team,
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=5),
        )
        task_instance = factories.TaskInstanceFactory(
            task=task, active_from=task.created_at
        )
        with mock.patch(
            "tasks.models.now",
            mock.Mock(return_value=task.created_at + datetime.timedelta(days=2)),
        ):
            completion = factories.TaskInstanceCompletionFactory(
                task_instance=task_instance, user_who_completed_task=self.member
            )

        now = task.created_at + datetime.timedelta(days=8)
        new_task_instance = TaskInstance.objects.filter(
            task=task, completed=False, deleted_at=None
        ).first()
        with mock.patch("common.models.timezone.now", mock.Mock(return_value=now)):
            second_completion = factories.TaskInstanceCompletionFactory(
                task_instance=new_task_instance, user_who_completed_task=self.member
            )
        new_task_instance.refresh_from_db()
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(self.member.id, self.team.id),
            completion.points_granted + second_completion.points_granted,
        )
        now = task.created_at + datetime.timedelta(days=9)
        with mock.patch("common.models.timezone.now", mock.Mock(return_value=now)):
            completion.delete()

        task_instance.refresh_from_db()
        self.assertTrue(task_instance.completed)
        with mock.patch(
            "tasks.models.now", mock.Mock(return_value=now + datetime.timedelta(days=2))
        ):
            self.assertFalse(new_task_instance.active)

        self.assertEqual(task_instance.deleted_at, now)
        self.assertEqual(TaskInstance.objects.filter(task=task).count(), 3)
        self.assertEqual(
            TaskInstance.objects.filter(
                task=task, completed=False, deleted_at=None
            ).count(),
            1,
        )
        another_new_task_instance = TaskInstance.objects.filter(
            task=task, completed=False, deleted_at=None
        ).first()
        with mock.patch("tasks.models.now", mock.Mock(return_value=now)):
            self.assertFalse(another_new_task_instance.active)
        self.assertNotEqual(
            another_new_task_instance.active_from, task_instance.active_from
        )
        self.assertNotEqual(another_new_task_instance.active_from, task.created_at)
        self.assertEqual(
            TaskInstanceCompletion.count_user_points(self.member.id, self.team.id),
            second_completion.points_granted,
        )

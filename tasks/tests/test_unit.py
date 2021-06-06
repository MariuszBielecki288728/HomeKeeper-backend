import datetime
import pytz

from parameterized import parameterized
from unittest import mock
from django.test import TestCase

from common.tests.factories import TaskFactoryNoSignals, TaskInstanceFactory


class TaskPrizeUnitTestCase(TestCase):
    def setUp(self):
        active_from = datetime.datetime(2018, 4, 2, 0, 0, 0, tzinfo=pytz.utc)
        task = TaskFactoryNoSignals(
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=1),
            base_points_prize=5,
        )
        self.task_instance = TaskInstanceFactory(task=task, active_from=active_from)

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
        task = TaskFactoryNoSignals(
            is_recurring=True,
            refresh_interval=datetime.timedelta(days=30),
            base_points_prize=15,
        )
        self.task_instance = TaskInstanceFactory(task=task, active_from=active_from)

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
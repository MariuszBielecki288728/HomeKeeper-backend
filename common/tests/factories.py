import factory
from faker import Faker

from django.utils import timezone
from django.contrib.auth import get_user_model

from common.models import TrackingFieldsMixin, ViewConfigurationFieldsMixin
from users.models import Profile
from teams.models import Team
from tasks.models import Task, TaskInstance, TaskInstanceCompletion
from tasks import signals

faker = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: faker.unique.user_name() + f"{n}")
    email = faker.email()
    password = faker.password(length=32)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class ViewConfigurationFieldsMixinFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ViewConfigurationFieldsMixin
        abstract = True

    image_id = faker.text(max_nb_chars=10)
    color_id = faker.text(max_nb_chars=10)


@factory.django.mute_signals(signals.post_save)
class ProfileFactory(ViewConfigurationFieldsMixinFactory):
    class Meta:
        model = Profile

    # We pass in profile=None to prevent UserFactory from creating another profile
    # (this disables the RelatedFactory)
    user = factory.SubFactory(
        "common.tests.factories.UserFactoryNoSignals", profile=None
    )


@factory.django.mute_signals(signals.post_save)
class UserFactoryNoSignals(UserFactory):
    """
    Factory that should be used when one wants to create Profile manually (or by factory).
    """

    profile = factory.RelatedFactory(ProfileFactory, factory_related_name="user")


class TrackingFieldsMixinFactory(factory.django.DjangoModelFactory):
    """
    Note: auto_now_add overwrites created_at value.
          It should be improved in the future.
    """

    class Meta:
        model = TrackingFieldsMixin
        abstract = True

    created_at = faker.past_datetime(tzinfo=timezone.get_current_timezone())
    created_by = factory.SubFactory(UserFactoryNoSignals)


class TeamFactory(TrackingFieldsMixinFactory):
    class Meta:
        model = Team

    name = faker.text(max_nb_chars=50)
    members = factory.SubFactory(UserFactoryNoSignals)
    password = faker.password(length=32)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_team(*args, **kwargs)

    @factory.post_generation
    def members(self, create, extracted):
        if not create:
            return

        self.members.add(self.created_by)
        if extracted:
            for member in extracted:
                self.members.add(member)


class TaskFactory(TrackingFieldsMixinFactory):
    class Meta:
        model = Task

    name = faker.text(max_nb_chars=50)
    description = faker.text(max_nb_chars=200)
    team = factory.SubFactory(TeamFactory)
    base_points_prize = faker.pyint()


@factory.django.mute_signals(signals.post_save)
class TaskFactoryNoSignals(TaskFactory):
    """
    Factory that should be used when one wants to create
    TaskInstance manually (or by factory).
    """

    pass


class TaskInstanceFactory(TrackingFieldsMixinFactory):
    class Meta:
        model = TaskInstance

    task = factory.SubFactory(TaskFactoryNoSignals)
    active_from = factory.LazyAttribute(lambda a: a.created_at)


class TaskInstanceCompletionFactory(TrackingFieldsMixinFactory):
    class Meta:
        model = TaskInstanceCompletion

    task_instance = factory.SubFactory(TaskInstanceFactory)
    user_who_completed_task = factory.SubFactory(UserFactoryNoSignals)

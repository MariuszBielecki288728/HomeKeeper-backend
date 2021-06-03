import graphene

from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django import DjangoObjectType
from graphql.error.graphql_error import GraphQLError
from graphql.type import GraphQLResolveInfo
from graphql_jwt.decorators import login_required

from tasks.forms import TaskCreationForm, TaskInstanceCompletionForm
from tasks.models import Task, TaskInstance, TaskInstanceCompletion
from tasks.scalars import Duration

from teams.models import Team


class TaskType(DjangoObjectType):
    refresh_interval = graphene.Field(Duration)
    active = graphene.Field(graphene.Boolean())

    class Meta:
        model = Task
        fields = (
            "id",
            "name",
            "description",
            "team",
            "base_points_prize",
            "refresh_interval",
            "is_recurring",
            "active",
        )


class TaskInstanceType(DjangoObjectType):
    active = graphene.Field(graphene.Boolean())

    class Meta:
        model = TaskInstance
        fields = ("id", "task", "active_from", "completed", "active")


class TaskInstanceCompletionType(DjangoObjectType):
    class Meta:
        model = TaskInstanceCompletion
        fields = "__all__"


class CreateTask(DjangoModelFormMutation):
    task = graphene.Field(TaskType)

    class Meta:
        form_class = TaskCreationForm

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        team = Team.objects.get(pk=input.team)
        if not team.members.filter(id=info.context.user.id).exists():
            raise GraphQLError("Only members of the given team may create tasks")
        return super().mutate(root, info, input)

    @classmethod
    def perform_mutate(cls, form, info):
        obj = form.save()
        obj.created_by = info.context.user
        obj.save()
        kwargs = {cls._meta.return_field_name: obj}
        return cls(errors=[], **kwargs)


class RemoveTask:
    pass


class SubmitTaskInstanceCompletion(DjangoModelFormMutation):
    taskInstanceCompletion = graphene.Field(TaskInstanceCompletionType)

    class Meta:
        form_class = TaskInstanceCompletionForm

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
        task_instance = TaskInstance.objects.get(pk=input.task_instance)
        Team.check_membership(info.context.user, task_instance.task.team.id)
        if task_instance.completed or task_instance.deleted_at:
            raise GraphQLError("This task instance is already completed or deleted")
        return super().mutate(root, info, input)

    @classmethod
    def perform_mutate(cls, form, info):
        obj = form.save(commit=False)
        obj.user_who_completed_task = obj.created_by = info.context.user
        obj.save()
        kwargs = {cls._meta.return_field_name: obj}
        return cls(errors=[], **kwargs)


class RevertTaskCompletion:
    pass


class Query(graphene.ObjectType):
    tasks = graphene.Field(
        graphene.List(TaskType),
        team_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
    )
    task_instances = graphene.Field(
        graphene.List(TaskInstanceType),
        team_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
    )
    related_task_instances = graphene.Field(
        graphene.List(TaskInstanceType),
        task_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
    )
    completions = graphene.Field(
        graphene.List(TaskInstanceCompletionType),
        team_id=graphene.Int(required=True),
    )
    user_points = graphene.Field(
        graphene.Int(),
        team_id=graphene.Int(required=True),
    )

    @login_required
    def resolve_tasks(
        self, info: GraphQLResolveInfo, team_id: int, only_active: bool = False
    ):
        Team.check_membership(info.context.user, team_id)
        tasks = Task.objects.filter(team=team_id)
        return [t for t in tasks.all() if t.active] if only_active else tasks

    @login_required
    def resolve_task_instances(
        self, info: GraphQLResolveInfo, team_id: int, only_active: bool = False
    ):
        Team.check_membership(info.context.user, team_id)
        task_instances = TaskInstance.objects.filter(task__team=team_id)
        return (
            [t for t in task_instances.all() if t.active]
            if only_active
            else task_instances
        )

    @login_required
    def resolve_related_task_instances(
        self, info: GraphQLResolveInfo, task_id: int, only_active: bool = False
    ):
        task_instances = TaskInstance.objects.filter(task=task_id)
        return (
            [t for t in task_instances.all() if t.active]
            if only_active
            else task_instances
        )


class Mutation(graphene.ObjectType):
    create_task = CreateTask.Field()
    submit_task_instance_completion = SubmitTaskInstanceCompletion.Field()

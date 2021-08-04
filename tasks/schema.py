import graphene

from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoSerializerMutation

from graphql.type import GraphQLResolveInfo
from graphql_jwt.decorators import login_required

from common.schema import AuthDjangoSerializerMutationMixin
from tasks.models import Task, TaskInstance, TaskInstanceCompletion
from tasks.serializers import TaskSerializer, TaskInstanceCompletionSerializer

from teams.models import Team

from users.schema import UserType


class TaskType(DjangoObjectType):
    # make Graphene serialize interval to human-readable form
    refresh_interval = graphene.Field(graphene.String())
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
    current_prize = graphene.Field(graphene.Int())

    class Meta:
        model = TaskInstance
        fields = (
            "id",
            "task",
            "active_from",
            "completed",
            "active",
            "deleted_at",
            "current_prize",
        )


class TaskInstanceCompletionType(DjangoObjectType):
    active = graphene.Field(graphene.Boolean())

    class Meta:
        model = TaskInstanceCompletion
        fields = (
            "id",
            "task_instance",
            "user_who_completed_task",
            "points_granted",
            "active",
            "created_at",
            "deleted_at",
        )


class TaskSerializerMutation(
    AuthDjangoSerializerMutationMixin, DjangoSerializerMutation
):
    task = graphene.Field(TaskType)

    class Meta:
        description = "DRF serializer based Mutation for Tasks."
        serializer_class = TaskSerializer
        only_fields = [
            "id",
            "name",
            "description",
            "team",
            "base_points_prize",
            "refresh_interval",
            "is_recurring",
        ]
        input_field_name = "input"


class TaskInstanceCompletionSerializerMutation(
    AuthDjangoSerializerMutationMixin, DjangoSerializerMutation
):
    taskInstanceCompletion = graphene.Field(TaskInstanceCompletionType)

    class Meta:
        description = "DRF serializer based Mutation for TaskInstanceCompletions."
        serializer_class = TaskInstanceCompletionSerializer
        only_fields = [
            "id",
            "task_instance",
        ]
        input_field_name = "input"
        output_field_name = "taskInstanceCompletion"


class MemberPointsType(graphene.ObjectType):
    member = graphene.Field(UserType())
    points = graphene.Int()


class Query(graphene.ObjectType):
    tasks = graphene.Field(
        graphene.List(TaskType),
        team_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
        description="Lists Tasks in the given team.",
    )
    task_instances = graphene.Field(
        graphene.List(TaskInstanceType),
        team_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
        description="Lists TaskIntances in the given team.",
    )
    related_task_instances = graphene.Field(
        graphene.List(TaskInstanceType),
        task_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
        description="Lists TaskIntances of the given task.",
    )
    completions = graphene.Field(
        graphene.List(TaskInstanceCompletionType),
        team_id=graphene.Int(required=True),
        only_active=graphene.Boolean(default_value=False),
        description="Lists history of TaskInsance completions in the given team.",
    )
    user_points = graphene.Field(
        graphene.Int(),
        user_id=graphene.Int(required=True),
        team_id=graphene.Int(required=True),
        from_datetime=graphene.DateTime(),
        to_datetime=graphene.DateTime(),
        description="""Counts points for a given user in a given team.
            User has to be a member of the given team.
            Logged in user has to be member of the given team.
        """,
    )
    team_members_points = graphene.Field(
        graphene.List(MemberPointsType),
        team_id=graphene.Int(required=True),
        from_datetime=graphene.DateTime(),
        to_datetime=graphene.DateTime(),
        description="""Counts points for each member of a given team.
            Logged in user has to be member of the given team.
        """,
    )

    @login_required
    def resolve_tasks(
        self, info: GraphQLResolveInfo, team_id: int, only_active: bool = False
    ):
        Team.check_membership(info.context.user.id, team_id)
        tasks = Task.objects.filter(team=team_id)
        return [t for t in tasks.all() if t.active] if only_active else tasks

    @login_required
    def resolve_task_instances(
        self, info: GraphQLResolveInfo, team_id: int, only_active: bool = False
    ):
        Team.check_membership(info.context.user.id, team_id)
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

    def resolve_completions(
        self, info: GraphQLResolveInfo, team_id: int, only_active: bool = False
    ):
        task_completions = TaskInstanceCompletion.objects.filter(
            task_instance__task__team=team_id
        ).order_by("-created_at")

        return (
            [t for t in task_completions.all() if t.active]
            if only_active
            else task_completions
        )

    def resolve_user_points(
        self,
        info: GraphQLResolveInfo,
        user_id: int,
        team_id: int,
        from_datetime: bool = None,
        to_datetime: bool = None,
    ):
        Team.check_membership(info.context.user.id, team_id)
        Team.check_membership(user_id, team_id)
        return TaskInstanceCompletion.count_user_points(
            user_id, team_id, from_datetime, to_datetime
        )

    def resolve_team_members_points(
        self,
        info: GraphQLResolveInfo,
        team_id: int,
        from_datetime: bool = None,
        to_datetime: bool = None,
    ):
        Team.check_membership(info.context.user.id, team_id)
        team = Team.objects.get(id=team_id)
        return [
            MemberPointsType(
                member,
                TaskInstanceCompletion.count_user_points(
                    member.id, team.id, from_datetime, to_datetime
                ),
            )
            for member in team.members.all()
        ]


class Mutation(graphene.ObjectType):
    create_task = TaskSerializerMutation.CreateField()
    update_task = TaskSerializerMutation.UpdateField()
    delete_task = TaskSerializerMutation.DeleteField()

    submit_task_instance_completion = (
        TaskInstanceCompletionSerializerMutation.CreateField()
    )
    revert_task_instance_completion = (
        TaskInstanceCompletionSerializerMutation.DeleteField()
    )

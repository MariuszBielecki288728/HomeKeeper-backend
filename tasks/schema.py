import graphene

from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django import DjangoObjectType
from graphql.error.graphql_error import GraphQLError
from graphql_jwt.decorators import login_required

from tasks.forms import TaskCreationForm
from tasks.models import Task

from teams.models import Team


class TaskType(DjangoObjectType):
    class Meta:
        model = Task
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


class Query(graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    create_task = CreateTask.Field()

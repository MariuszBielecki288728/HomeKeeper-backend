import graphene

from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError


from tasks.forms import TaskCreationForm
from tasks.models import Task


class TaskType(DjangoObjectType):
    class Meta:
        model = Task
        fields = "__all__"


class CreateTask(DjangoModelFormMutation):
    pet = graphene.Field(TaskType)

    class Meta:
        form_class = TaskCreationForm

    @classmethod
    @login_required
    def mutate(cls, root, info, input):
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

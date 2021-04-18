from django.contrib.auth import get_user_model
from users.forms import RegisterForm

import graphene
from graphene_django.forms.mutation import DjangoFormMutation
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class Register(DjangoFormMutation):
    class Meta:
        form_class = RegisterForm

    # @classmethod
    # @login_required
    # def mutate(cls, *args, **kwargs):
    #     super().mutate(*args, **kwargs)


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()

    @login_required
    def resolve_me(self, info):
        return info.context.user


class Mutation(graphene.ObjectType):
    register = Register.Field()

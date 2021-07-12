from django.contrib.auth import get_user_model
from users.forms import RegisterForm

import graphene
from graphene_django.forms.mutation import DjangoFormMutation
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


# FIXME: Register Mutation returns RegisterPayload which contains
# unecrypted user password!
class Register(DjangoFormMutation):
    class Meta:
        form_class = RegisterForm


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)

    @login_required
    def resolve_me(self, info):
        return info.context.user


class Mutation(graphene.ObjectType):
    register = Register.Field()

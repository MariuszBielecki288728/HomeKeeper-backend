import graphene

from django.contrib.auth import get_user_model
from graphene_django.forms.mutation import DjangoFormMutation
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from users.forms import RegisterForm
from users.models import Profile

from teams.models import Team


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class UserType(DjangoObjectType):
    profile = graphene.Field(ProfileType)

    class Meta:
        model = get_user_model()


# FIXME: Register Mutation returns RegisterPayload which contains
# unecrypted user password!
class Register(DjangoFormMutation):
    class Meta:
        form_class = RegisterForm


class ProfileInput(graphene.InputObjectType):
    user_id = graphene.ID()
    image_id = graphene.String()
    color_id = graphene.String()


class SetProfileData(graphene.Mutation):
    class Arguments:
        input = ProfileInput(required=True)

    profile = graphene.Field(ProfileType)

    @login_required
    def mutate(root, info, input):
        """
        Sets users profile data.
        Currently user can change profile info of users
        who are members of the same team as him.
        """
        if input.user_id:
            Team.check_users_in_the_same_team(info.context.user.id, input.user_id)
            user_to_change = input.user_id
        else:
            user_to_change = info.context.user.id

        prof = get_user_model().objects.get(id=user_to_change).profile
        prof.image_id = input.image_id or prof.image_id
        prof.color_id = input.color_id or prof.color_id
        prof.save()

        return SetProfileData(profile=prof)


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)

    @login_required
    def resolve_me(self, info):
        return info.context.user


class Mutation(graphene.ObjectType):
    register = Register.Field()
    set_profile_data = SetProfileData.Field()

import graphene
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError

from teams.models import Team
from teams.forms import TeamForm


class TeamType(DjangoObjectType):
    class Meta:
        model = Team
        exclude = ("password",)


class CreateTeam(DjangoModelFormMutation):
    team = graphene.Field(TeamType)

    class Meta:
        form_class = TeamForm

    @classmethod
    @login_required
    def mutate(cls, *args, **kwargs):
        return super().mutate(*args, **kwargs)

    @classmethod
    def perform_mutate(cls, form, info):
        obj = form.save()
        obj.created_by = info.context.user
        obj.save()
        kwargs = {cls._meta.return_field_name: obj}
        return cls(errors=[], **kwargs)


class JoinTeam(graphene.Mutation):
    team = graphene.Field(TeamType)

    class Arguments:
        team_id = graphene.Int()
        password = graphene.String()

    @login_required
    def mutate(root, info, team_id, password):
        team = Team.objects.get(pk=team_id)
        user = info.context.user

        # TODO move this checks to Form (clean method?)
        if team.members.filter(pk=user.id):
            raise GraphQLError(f"You are already member of {team.name}")
        if not team.check_password(password):
            raise GraphQLError(f"Wrong password for {team.name}")

        team.members.add(user)
        return JoinTeam(team=team)


class LeaveTeam(graphene.Mutation):
    team = graphene.Field(TeamType)

    class Arguments:
        team_id = graphene.Int()

    @login_required
    def mutate(root, info, team_id=None):
        user = info.context.user

        if team_id is None:
            teams = Team.objects.filter(members=user)
        else:
            teams = Team.objects.filter(pk=team_id).filter(members=user)

        if not teams:
            raise GraphQLError(
                "You are not a member of the team or the given team does not exist."
            )

        teams[0].members.remove(user)
        return JoinTeam(team=teams[0])


class Query(graphene.ObjectType):
    my_teams = graphene.List(TeamType)
    teams = graphene.List(TeamType)

    def resolve_teams(self, info):
        return Team.objects.all()

    @login_required
    def resolve_my_teams(self, info):
        return Team.objects.filter(members=info.context.user)


class Mutation(graphene.ObjectType):
    create_team = CreateTeam.Field()
    join_team = JoinTeam.Field()
    leave_team = LeaveTeam.Field()

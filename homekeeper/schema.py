import graphene
import graphql_jwt

from django.db import transaction

from users import schema as users_schema
from teams import schema as teams_schema
from tasks import schema as tasks_schema


class AtomicSchema(graphene.Schema):
    # Hack for https://github.com/graphql-python/graphene-django/issues/1190
    def execute(self, *args, **kwargs):
        with transaction.atomic():
            result = super().execute(*args, **kwargs)
            if result.errors:
                transaction.set_rollback(True)
            return result


class Query(
    teams_schema.Query, users_schema.Query, tasks_schema.Query, graphene.ObjectType
):
    pass


class Mutation(
    teams_schema.Mutation,
    users_schema.Mutation,
    tasks_schema.Mutation,
    graphene.ObjectType,
):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = AtomicSchema(query=Query, mutation=Mutation)

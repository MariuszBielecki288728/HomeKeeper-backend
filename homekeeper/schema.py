import graphene
import graphql_jwt

from users import schema as users_schema
from teams import schema as teams_schema


class Query(teams_schema.Query, users_schema.Query, graphene.ObjectType):
    pass


class Mutation(
    teams_schema.Mutation,
    users_schema.Mutation,
    graphene.ObjectType,
):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)

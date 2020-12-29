import graphene
import graphql_jwt

from users import schema as users_schema


class Query(users_schema.Query, graphene.ObjectType):
    pass


class Mutation(
    users_schema.Mutation,
    graphene.ObjectType,
):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)

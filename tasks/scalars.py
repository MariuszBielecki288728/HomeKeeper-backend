from graphene.types import Scalar
from graphql.language import ast
from django.utils.dateparse import parse_duration


class Duration(Scalar):
    """Duration Scalar"""

    @staticmethod
    def serialize(timedelta):
        return str(timedelta)

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return parse_duration(node.value)

    @staticmethod
    def parse_value(value):
        return parse_duration(value)

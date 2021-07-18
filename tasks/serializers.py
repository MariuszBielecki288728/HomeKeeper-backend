from rest_framework import serializers
from tasks.models import Task
from graphql.error.graphql_error import GraphQLError


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        if self.instance is not None and data["team"] is not None:
            raise GraphQLError("Can't change team on already existing task")
        if self.instance is not None:
            return data
        if not data["team"].members.filter(id=self.context["request"].user.id).exists():
            raise GraphQLError("Only members of the given team may create tasks")
        return data

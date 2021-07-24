from rest_framework import serializers
from graphql.error.graphql_error import GraphQLError

from tasks.models import Task, TaskInstanceCompletion
from teams.models import Team


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


class TaskInstanceCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskInstanceCompletion
        fields = "__all__"
        extra_kwargs = {
            "user_who_completed_task": {"required": False, "allow_null": True},
            "points_granted": {"required": False},
        }

    def validate(self, data):
        task_instance = data["task_instance"]
        Team.check_membership(
            self.context["request"].user.id, task_instance.task.team.id
        )
        if task_instance.completed or task_instance.deleted_at:
            raise GraphQLError("This task instance is already completed or deleted")
        return data

    def create(self, validated_data):
        validated_data["user_who_completed_task"] = self.context["request"].user
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

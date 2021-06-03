from django.contrib import admin

from tasks.models import Task, TaskInstance, TaskInstanceCompletion

admin.site.register(Task)
admin.site.register(TaskInstance)
admin.site.register(TaskInstanceCompletion)
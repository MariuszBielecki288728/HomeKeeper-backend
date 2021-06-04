from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TasksConfig(AppConfig):
    name = "tasks"
    verbose_name = _("tasks")

    def ready(self):
        import tasks.signals  # noqa

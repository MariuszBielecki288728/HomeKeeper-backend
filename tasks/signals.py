from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from tasks.models import Task, TaskInstance


@receiver(post_save, sender=Task)
def create_task_instance(sender, instance, created, **kwargs):
    if created:
        TaskInstance.objects.create(task=instance, active_from=timezone.now())

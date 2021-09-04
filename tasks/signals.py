from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.utils import timezone

from tasks.models import Task, TaskInstance, TaskInstanceCompletion


@receiver(post_save, sender=Task)
def create_task_instance(sender, instance: Task, created, **kwargs):
    if created:
        TaskInstance.objects.create(task=instance, active_from=timezone.now())


@receiver(post_save, sender=TaskInstanceCompletion)
def update_task_instance_on_completion(
    sender, instance: TaskInstanceCompletion, created, **kwargs
):
    """
    Handles creating and updating task instances upon completing or deleting a completion.
    On single occurrence tasks it marks task_instance as completed or not completed
    (when deleting a completion). On reccurrent tasks it creates a new task_instance
    upon completion.
    When completion is deleted, and there exists a task instance that is next
    in the timeline, then it modifies it to make it active from the date that
    the completed task_instance was active from.
    """
    if created:
        list(
            TaskInstance.objects.filter(
                id=instance.task_instance.id
            ).select_for_update()
        )
        with transaction.atomic():
            instance.task_instance.refresh_from_db()
            if instance.task_instance.completed is True:
                raise RuntimeError("TaskInstance is already completed")
        instance.task_instance.completed = True
        instance.task_instance.save()
        if (
            instance.task_instance.task.is_recurring
            and instance.task_instance.task.refresh_interval
        ):
            TaskInstance.objects.create(
                task=instance.task_instance.task,
                active_from=(
                    timezone.now() + instance.task_instance.task.refresh_interval
                ),
            )
    elif instance.deleted_at is not None:
        if TaskInstance.objects.filter(
            task=instance.task_instance.task,
            completed=True,
            active_from__gt=instance.task_instance.active_from,
            deleted_at=None,
        ).exists():
            instance.task_instance.delete()
            return  # if there is completed instance since then, just delete task_instance.

        future_task_instance = (
            TaskInstance.objects.select_for_update()
            .filter(task=instance.task_instance.task, completed=False, deleted_at=None)
            .order_by("active_from")
            .first()
        )
        if future_task_instance is not None:
            instance.task_instance.delete()
            future_task_instance.active_from = instance.task_instance.active_from
            future_task_instance.save()
        else:
            instance.task_instance.completed = False
            instance.task_instance.save()

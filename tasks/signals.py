from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from tasks.models import Task, TaskInstance, TaskInstanceCompletion


@receiver(post_save, sender=Task)
def create_task_instance(sender, instance, created, **kwargs):
    if created:
        TaskInstance.objects.create(task=instance, active_from=timezone.now())


@receiver(post_save, sender=TaskInstanceCompletion)
def update_task_instance_on_completion(
    sender, instance: TaskInstanceCompletion, created, **kwargs
):
    if created:
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
    # elif instance.deleted_at is not None:
    #     instance.task_instance.deleted_at = timezone.now()
    #     instance.task_instance.save()

    #     future_task_instance = (
    #         TaskInstance.objects.select_for_update()
    #         .filter(task=instance.task_instance.task, completed=False, deleted_at=None)
    #         .order_by("active_from")
    #         .first()
    #     )
    #     if future_task_instance:
    #         future_task_instance.active_from = instance.task_instance.active_from
    #     else:
    #         TaskInstance.objects.create(
    #             task=instance.task_instance.task,
    #             active_from=instance.task_instance.active_from,
    #         )
    #     # TODO when the completion is deleted - delete completed
    #     # task_instance and change active_from to the
    #     # previous active_from on the new task_instance

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from users.models import Profile


@receiver(post_save, sender=get_user_model())
def create_task_instance(sender, instance: get_user_model(), created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

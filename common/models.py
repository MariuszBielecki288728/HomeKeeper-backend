from django.db import models
from django.db import transaction
from django.conf import settings
from django.utils import timezone


class TrackingFieldsMixin(models.Model):

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None, blank=True)

    def delete(self):
        """
        Deletes object softly, note that it is not called at deletion
        via object manager or querysets! If needed, it may be improved in the future:
        https://adriennedomingus.com/blog/soft-deletion-in-django
        """

        with transaction.atomic():
            list(self.__class__.objects.filter(id=self.id).select_for_update())
            self.refresh_from_db()
            if self.deleted_at is not None:
                raise RuntimeError(f"{self} is already deleted")
            self.deleted_at = timezone.now()
            self.save()

    @property
    def active(self):
        return self.deleted_at is None

    class Meta:
        abstract = True


class ViewConfigurationFieldsMixin(models.Model):
    """
    Fields that should be used by clients to reference local
    objects, e.g. profile image
    """

    image_id = models.CharField(max_length=10, null=True, blank=True)
    color_id = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        abstract = True

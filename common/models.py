from django.db import models
from django.conf import settings


class TrackingFieldsMixin(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

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

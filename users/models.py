from django.db import models
from django.contrib.auth import get_user_model

from common.models import ViewConfigurationFieldsMixin


class Profile(ViewConfigurationFieldsMixin):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

from django.forms import ModelForm

from teams.models import Team


class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ["name"]

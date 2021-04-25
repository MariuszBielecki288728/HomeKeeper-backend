from django import forms

from teams.models import Team


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "password"]
        widgets = {
            "password": forms.PasswordInput(),
        }

    def save(self, commit=True):
        team = super().save(commit=False)
        team.set_password(team.password)
        if commit:
            team.save()
        return team

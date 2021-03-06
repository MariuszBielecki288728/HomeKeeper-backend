# Generated by Django 3.1.3 on 2020-12-29 00:30

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField()),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=300)),
                ('base_points_prize', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('refresh_interval', models.DurationField()),
                ('is_reoccuring', models.BooleanField()),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.team')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

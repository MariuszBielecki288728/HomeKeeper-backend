# Generated by Django 3.2.3 on 2021-06-03 16:37

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0006_auto_20210425_0029"),
    ]

    operations = [
        migrations.AlterField(
            model_name="team",
            name="name",
            field=models.CharField(
                max_length=50, validators=[django.core.validators.MinLengthValidator(1)]
            ),
        ),
    ]

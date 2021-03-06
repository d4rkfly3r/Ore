# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-04 18:08
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import ore.core.util


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0002_version_channel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='name',
            field=models.CharField(max_length=32, validators=[django.core.validators.RegexValidator('^[\\w.\\-_]+([\\w.-_ ]*[\\w.\\-_]+)?$', 'Enter a valid version name.', 'invalid'), ore.core.util.validate_not_prohibited], verbose_name='name'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-05 04:31
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import ore.core.util


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_auto_20160104_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=32, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9._][a-zA-Z0-9.\\-_]*$', 'Enter a valid project name.', 'invalid'), ore.core.util.validate_not_prohibited], verbose_name='name'),
        ),
    ]

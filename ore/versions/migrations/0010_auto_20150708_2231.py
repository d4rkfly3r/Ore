# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0009_auto_20150708_2226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='is_primary',
            field=models.NullBooleanField(default=None),
        ),
    ]

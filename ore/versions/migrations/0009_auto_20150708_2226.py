# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0008_version_channel'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='is_primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='file',
            unique_together=set([('project', 'version', 'file_name', 'file_extension'), ('project', 'version', 'is_primary')]),
        ),
    ]

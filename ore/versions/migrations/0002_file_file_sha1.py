# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='file_sha1',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]

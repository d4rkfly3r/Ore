# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0003_auto_20150629_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_sha1',
            field=models.CharField(max_length=40),
        ),
    ]

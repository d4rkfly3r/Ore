# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0004_auto_20150629_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_extension',
            field=models.CharField(verbose_name='extension', blank=True, max_length=12),
        ),
    ]

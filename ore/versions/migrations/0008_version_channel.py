# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0007_auto_20150708_1812'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='channel',
            field=models.ForeignKey(to='versions.Channel', related_name='versions', default=1),
            preserve_default=False,
        ),
    ]

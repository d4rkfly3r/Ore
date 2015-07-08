# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def generate_channels(apps, schema_editor):
    Channel = apps.get_model('versions', 'Channel')
    Channel(
        project=None,
        name='Release',
        colour='#48c3ce'
    ).save()
    Channel(
        project=None,
        name='Snapshot',
        colour='#ce427a'
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0006_auto_20150708_1801'),
    ]

    operations = [
        migrations.RunPython(generate_channels),
    ]

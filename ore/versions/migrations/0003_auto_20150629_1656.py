# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import hashlib


def set_file_sha1(apps, schema_editor):
    File = apps.get_model("versions", "File")
    for file in File.objects.all():
        s = hashlib.sha1()
        f = file.file.file
        for chunk in f.chunks():
            s.update(chunk)
        file.file_sha1 = s.hexdigest()
        file.save()


def do_nothing(apps, schema_editor):
    # migrating backwards is a no-op
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('versions', '0002_file_file_sha1'),
    ]

    operations = [
        migrations.RunPython(set_file_sha1, do_nothing),
    ]

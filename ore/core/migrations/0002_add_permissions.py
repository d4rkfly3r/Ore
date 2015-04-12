# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

PROJECT_PERMISSIONS = [
    ('version.create', 'Create new versions'),
    ('version.edit', 'Edit versions'),
    ('version.delete', 'Delete versions'),

    ('file.create', 'Upload new files'),
    ('file.edit', 'Edit files'),
    ('file.delete', 'Delete files'),

    ('project.edit', 'Edit a project'),
    ('project.rename', 'Change a project\'s name'),
    ('project.transfer', 'Transfer a project to a different user or organization'),
    ('project.delete', 'Delete a project'),

    ('project.team.create', 'Create a new project team'),
    ('project.team.delete', 'Delete a project team'),
    ('project.team.edit', 'Edit a project team\'s name or description'),
    ('project.team.manage', 'Manage the members of a project team'),
]
ORGANIZATION_PERMISSIONS = [
    ('project.create', 'Create a new project'),

    ('org.team.create', 'Create a new organization team'),
    ('org.team.edit', 'Edit a organization team\'s name or description'),
    ('org.team.manage', 'Manage the members of an organization team'),
    ('org.team.delete', 'Delete an organization team'),
]

def forwards_func(apps, schema_editor):
    Permission = apps.get_model("core", "Permission")
    for slug, name in PROJECT_PERMISSIONS:
        Permission.objects.create(slug=slug, name=name, description='', applies_to_project=True)
    for slug, name in ORGANIZATION_PERMISSIONS:
        Permission.objects.create(slug=slug, name=name, description='', applies_to_project=False)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            forwards_func,
        ),
    ]
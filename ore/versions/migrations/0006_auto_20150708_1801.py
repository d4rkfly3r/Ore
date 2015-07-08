# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ore.core.util
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20150624_0445'),
        ('versions', '0005_auto_20150629_1741'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(validators=[django.core.validators.RegexValidator('^[\\w.@+-]+([\\w.@+ -]*[\\w.@+-]+)?$', 'Enter a valid version name.', 'invalid'), ore.core.util.validate_not_prohibited], verbose_name='name', max_length=32)),
                ('colour', models.CharField(validators=[django.core.validators.RegexValidator('^#[0-9a-f]{6}$', 'Enter a valid HTML colour (e.g. #af0000)', 'invalid')], verbose_name='colour', max_length=7)),
                ('project', models.ForeignKey(null=True, blank=True, to='projects.Project', related_name='channels')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='file',
            unique_together=set([('project', 'version', 'file_name', 'file_extension')]),
        ),
    ]

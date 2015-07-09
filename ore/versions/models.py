from django.core import validators
from django.core.urlresolvers import reverse
from django.db import models

from django.db.models import Q
from model_utils import Choices
from model_utils.fields import StatusField
from ore.core.util import validate_not_prohibited, UserFilteringManager, prefix_q
from ore.projects.models import Project
from ore.util import ColourGenerator
from ore.core.regexs import TRIM_NAME_REGEX
import reversion


@reversion.register
class Version(models.Model):
    STATUS = Choices('active', 'deleted')
    status = StatusField()

    name = models.CharField('name', max_length=32,
                            validators=[
                                validators.RegexValidator(
                                    TRIM_NAME_REGEX, 'Enter a valid version name.', 'invalid'),
                                validate_not_prohibited,
                            ])
    description = models.TextField('description')
    project = models.ForeignKey(Project, related_name='versions')
    channel = models.ForeignKey('Channel', related_name='versions')

    objects = UserFilteringManager()

    @classmethod
    def is_visible_q(cls, prefix, user):
        if user.is_superuser:
            return Q()

        return Project.is_visible_q(prefix + 'project__', user) & (
            (
                prefix_q(prefix, status='active') &
                ~prefix_q(prefix, files__exact=None)
            ) | cls.is_visible_if_hidden_q(prefix, user)
        )

    @staticmethod
    def is_visible_if_hidden_q(prefix, user):
        if user.is_anonymous():
            return Q()

        return ~prefix_q(prefix, status='deleted') & Project.is_visible_if_hidden_q(prefix + 'project__', user)

    def __repr__(self):
        return '<Version %s of %s>' % (self.name, self.project.name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('repo-versions-detail',
                       kwargs={'namespace': self.project.namespace.name, 'project': self.project.name,
                               'version': self.name})

    def get_absolute_manage_url(self):
        return reverse('repo-versions-manage',
                       kwargs={'namespace': self.project.namespace.name, 'project': self.project.name,
                               'version': self.name})

    def full_name(self):
        return "{}/{}".format(self.project.full_name(), self.name)

    def primary_file(self):
        qs = self.files.filter(is_primary=True)
        if qs.count():
            return qs.get()
        return None

    class Meta:
        ordering = ['-pk']
        unique_together = ('project', 'name')


def file_upload(instance, filename):
    import posixpath
    import uuid

    # namespace_name = instance.project.namespace.name
    # project_name = instance.project.name

    uuid_bit = uuid.uuid4().hex
    return posixpath.join('files', uuid_bit[0], uuid_bit[:2], uuid_bit, filename)


@reversion.register
class File(models.Model):
    STATUS = Choices('active', 'pending', 'deleted')
    status = StatusField()

    project = models.ForeignKey(Project, related_name='files')
    version = models.ForeignKey(
        Version, related_name='files', blank=True, null=True)

    file = models.FileField(
        upload_to=file_upload, blank=False, null=False, max_length=512)
    file_name = models.CharField(blank=False, null=False, max_length=512)
    file_extension = models.CharField(
        'extension', max_length=12, blank=True, null=False)
    file_size = models.PositiveIntegerField(null=True, blank=False)
    file_sha1 = models.CharField(blank=False, null=False, max_length=40)

    is_primary = models.NullBooleanField(null=True, default=None)

    objects = UserFilteringManager()

    @classmethod
    def is_visible_q(cls, prefix, user):
        if user.is_anonymous():
            return Version.is_visible_q(prefix + 'version__', user) & prefix_q(prefix, status='active')
        elif user.is_superuser:
            return Q()

        return Version.is_visible_q(prefix + 'version__', user) & (
            prefix_q(prefix, status='active') |
            cls.is_visible_if_hidden_q(prefix, user)
        )

    @staticmethod
    def is_visible_if_hidden_q(prefix, user):
        if user.is_anonymous():
            return Q()

        return ~prefix_q(prefix, status='deleted') & Version.is_visible_if_hidden_q(prefix + 'version__', user)

    def full_name(self):
        return "{}/{}".format(self.version.full_name(), str(self.file))

    def get_absolute_url(self):
        return reverse('repo-files-download',
                       kwargs={'namespace': self.version.project.namespace.name, 'project': self.version.project.name,
                               'version': self.version.name, 'file': self.file_name,
                               'file_extension': self.file_extension})

    def __repr__(self):
        if self.version:
            return '<File %s in %s of %s>' % (str(self.file), self.version.name, self.version.project.name)
        else:
            return '<File %s in %s>' % (str(self.file), self.project.name)

    def __str__(self):
        return str(self.file)

    def _update_file_sha1(self):
        import hashlib
        s = hashlib.sha1()
        f = self.file.file
        for chunk in f.chunks():
            s.update(chunk)
        self.file_sha1 = s.hexdigest()

    def _update_attrs(self):
        import posixpath
        self.file_name = posixpath.basename(self.file.name)
        self.file_size = self.file.size

        self._update_file_sha1()

    def save(self, *args, **kwargs):
        update_attrs = kwargs.pop('update_file_attrs', True)

        if update_attrs:
            self._update_attrs()

        super(File, self).save(*args, **kwargs)

    class Meta:
        ordering = ['is_primary', '-pk']
        unique_together = [
            ('project', 'version', 'file_name', 'file_extension'),
            ('project', 'version', 'is_primary')
        ]


class Channel(models.Model):

    project = models.ForeignKey(
        Project, related_name='channels', null=True, blank=True)
    name = models.CharField('name', max_length=32,
                            validators=[
                                validators.RegexValidator(
                                    TRIM_NAME_REGEX, 'Enter a valid version name.', 'invalid'),
                                validate_not_prohibited,
                            ])
    colour = models.CharField('colour', max_length=7, validators=[
        validators.RegexValidator(
            '^#[0-9a-f]{6}$', 'Enter a valid HTML colour (e.g. #af0000)', 'invalid'),
    ], default=lambda: ColourGenerator().generate())

    def __str__(self):
        return self.name

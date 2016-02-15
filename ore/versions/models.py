from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
from django.db.models import Q
from model_utils import Choices
from model_utils.fields import StatusField
from ore.core.util import validate_not_prohibited, UserFilteringManager, add_prefix
from ore.projects.models import Project, Channel
from ore.core.regexs import TRIM_NAME_REGEX
from ore.util import markdown, mavenversion
from reversion import revisions as reversion


@reversion.register
class Version(models.Model):
    STATUS = Choices('active', 'deleted')
    status = StatusField()

    name = models.CharField(max_length=32,
                            validators=[
                                validators.RegexValidator(
                                    TRIM_NAME_REGEX, 'Enter a valid version name.', 'invalid'),
                                validate_not_prohibited,
                            ],
                            verbose_name='Version name',
                            help_text='To ensure your versions are ordered correctly, please use a Maven-compatible version'
                            )
    ordering_id = models.IntegerField(null=False, default=0)
    description = models.TextField('Description')
    description_html = models.TextField('Description HTML', null=False, blank=True)
    project = models.ForeignKey(Project, related_name='versions')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    objects = UserFilteringManager()

    @classmethod
    def is_visible_q(cls, user):
        if user.is_superuser:
            return Q()

        return add_prefix('project', Project.is_visible_q(user)) & (
            Q(status='active') |
            cls.is_visible_if_hidden_q(user)
        )

    @staticmethod
    def is_visible_if_hidden_q(user):
        if user.is_anonymous():
            return Q()

        return ~Q(status='deleted') & add_prefix('project', Project.is_visible_if_hidden_q(user))

    def __str__(self):
        return '%s of %s' % (self.name, self.project.name)

    def get_absolute_url(self):
        return reverse('versions-detail',
                       kwargs={'namespace': self.project.namespace.name, 'project': self.project.name,
                               'version': self.name})

    def full_name(self):
        return "{}/{}".format(self.project.full_name(), self.name)

    @classmethod
    def recalculate_ordering_ids_for_project(cls, project):
        qs = cls.objects.select_for_update().filter(project=project)
        version_infos = [(i, mavenversion.ComparableVersion(x)) for i, x in qs.values_list('id', 'name')]
        new_version_infos = sorted(version_infos, key=lambda x: x[1])
        for n, (id_, _) in enumerate(new_version_infos):
            cls.objects.filter(project=project, id=id_).update(ordering_id=n)

    def save(self, *args, **kwargs):
        self.description_html = markdown.compile(self.description)
        ret = super().save(*args, **kwargs)
        Version.recalculate_ordering_ids_for_project(self.project)
        return ret

    class Meta:
        ordering = ['-ordering_id']
        unique_together = ('project', 'name')


def file_upload(instance, filename):
    import posixpath
    import uuid

    # namespace_name = instance.project.namespace.name
    # project_name = instance.project.name

    uuid_bit = uuid.uuid4().hex
    return posixpath.join('files', uuid_bit, filename)


@reversion.register
class File(models.Model):
    STATUS = Choices('active', 'deleted')
    status = StatusField()

    project = models.ForeignKey(Project, related_name='files')
    version = models.ForeignKey(
        Version, related_name='files', blank=True, null=True)

    file = models.FileField(
        upload_to=file_upload, blank=False, null=False, max_length=512)
    file_name = models.CharField(blank=False, null=False, max_length=512)
    file_extension = models.CharField(
        'extension', max_length=12, blank=False, null=False)
    file_size = models.PositiveIntegerField(null=True, blank=False)

    plugin_id = models.CharField(max_length=256, null=True, blank=True)
    plugin_dependencies = JSONField(default='{}')

    objects = UserFilteringManager()

    def clean(self):
        if self.file:
            import posixpath
            self.file_name, self.file_extension = posixpath.splitext(
                posixpath.basename(self.file.name))
            self.file_size = self.file.size

            if self.file_extension.lower() != '.jar':
                raise ValidationError({'file': "This file doesn't appear to be a Sponge plugin JAR."})

            from ore.util import plugalyzer
            self.file.open('rb')
            plugin_infos = plugalyzer.Plugalyzer.analyze(self.file)
            if len(plugin_infos) < 1:
                raise ValidationError({'file': "The file you have uploaded doesn't seem to be a Sponge plugin (there were no classes with the @Plugin annotation)"})
            elif len(plugin_infos) > 1:
                raise ValidationError({'file': "The file you have uploaded appears to have multiple instances of the @Plugin annotation, which is presently unsupported"})
            plugin_info = plugin_infos[0]
            self.plugin_id = plugin_info.data['id']
            self.plugin_dependencies = plugin_info.json_dependencies

            if self.version and plugin_info.data['version'] != self.version.name:
                raise ValidationError({'file': "The file you have uploaded has a version of '{}', which does not match the version you have given of '{}'.".format(
                    plugin_info.data['version'], self.version.name)})

    def validate_unique(self, exclude=None):
        if self.file:
            if self.file_extension.lower() != '.jar':
                return super().validate_unique(exclude=exclude)

            project_plugin_ids = File.objects.filter(project=self.project).values_list('plugin_id', flat=True)
            if project_plugin_ids and not any(plid == self.plugin_id for plid in project_plugin_ids):
                raise ValidationError(
                    {'file':
                     "The plugin ID '{}' is not the same as the plugin ID you have used previously for this project. If you need to change it, please contact an administrator or create a new project.".format(
                         self.plugin_id)
                     })

            if File.objects.exclude(project=self.project).filter(plugin_id=self.plugin_id).exists():
                raise ValidationError({'file': "The plugin ID '{}' is already in use by another project. Please pick a different one.".format(self.plugin_id)})

        return super().validate_unique(exclude=exclude)

    @classmethod
    def is_visible_q(cls, user):
        if user.is_anonymous():
            return add_prefix('version', Version.is_visible_q(user)) & Q(status='active')
        elif user.is_superuser:
            return Q()

        return add_prefix('version', Version.is_visible_q(user)) & (
            Q(status='active') |
            cls.is_visible_if_hidden_q(user)
        )

    @staticmethod
    def is_visible_if_hidden_q(user):
        if user.is_anonymous():
            return Q()

        return ~Q(status='deleted') & Version.is_visible_if_hidden_q(user)

    def full_name(self):
        return "{}/{}".format(self.version.full_name(), str(self.file))

    def __str__(self):
        return '%s in %s of %s' % (str(self.file), self.version.name, self.version.project.name)

    class Meta:
        ordering = ['-pk']

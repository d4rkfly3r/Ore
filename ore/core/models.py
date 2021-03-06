from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from model_utils import Choices
from model_utils.fields import StatusField
from ore.core.util import validate_not_prohibited, UserFilteringInheritanceManager, UserFilteringManager
from ore.core.regexs import EXTENDED_NAME_REGEX
from reversion import revisions as reversion


@reversion.register
class Namespace(models.Model):
    STATUS = Choices('active', 'deleted')
    status = StatusField()

    name = models.CharField('name', max_length=32, unique=True,
                            validators=[
                                validators.RegexValidator(EXTENDED_NAME_REGEX, 'Names can only contain letters, numbers, underscores and hyphens.',
                                                          'invalid'),
                                validate_not_prohibited,
                            ])
    lower_name = models.CharField(
        'name', max_length=32, unique=True, null=False, blank=True)

    objects = UserFilteringInheritanceManager()

    @staticmethod
    def is_visible_q(user):
        if user.is_anonymous():
            return Q(status='active')
        elif user.is_superuser:
            return Q()

        return (
            Q(status='active') |
            (
                ~Q(status='deleted') &
                (
                    Q(oreuser=user) |
                    Q(organization__teams__users=user)
                )
            )
        )

    def validate_unique(self, *args, **kwargs):
        lower_name = self.name.lower()
        qs = Namespace.objects.filter(lower_name=lower_name)
        if self.pk:
            qs = qs.exclude(id=self.pk)
        if qs.exists():
            raise ValidationError(
                {"name": "A namespace with this name already exists."})
        super(Namespace, self).validate_unique(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.lower_name = self.name.lower()
        return super(Namespace, self).save(*args, **kwargs)

    @property
    def is_visible(self):
        return self.status == self.STATUS.active

    def get_absolute_url(self):
        return reverse('core-namespace', kwargs={'namespace': self.name})

    def __str__(self):
        return self.name


@reversion.register
class Permission(models.Model):
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    description = models.TextField()
    applies_to_model = models.ForeignKey(
        ContentType, related_name='ore_permissions')

    def __str__(self):
        return self.slug


def organization_avatar_upload(instance, filename):
    import posixpath
    import uuid

    _, file_ext = posixpath.splitext(filename)
    final_filename = uuid.uuid4().hex + file_ext
    return posixpath.join('avatars', 'organization', instance.name, final_filename)


class Organization(Namespace):
    avatar_image = models.ImageField(
        upload_to=organization_avatar_upload, blank=True, null=True, default=None, verbose_name="Avatar")

    objects = UserFilteringManager()

    @staticmethod
    def is_visible_q(user):
        if user.is_anonymous():
            return Q(status='active')
        elif user.is_superuser:
            return Q()

        return (
            Q(status='active') |
            (
                ~Q(status='deleted') &
                Q(teams__users=user)
            )
        )

    @property
    def avatar(self):
        if self.avatar_image:
            return self.avatar_image.url
        return "//www.gravatar.com/avatar/mysteryman?f=y&d=mm"

    def members(self):
        from ore.accounts.models import OreUser

        if self.name == 'platform':
            return OreUser.objects.filter(is_staff=True)

        return OreUser.objects.filter(organizationteams__organization=self).distinct()

    def user_has_permission(self, user, perm_slug, project=None):
        if isinstance(user, AnonymousUser):
            return False
        elif user.is_superuser:
            return True

        ownerships = user.__dict__.setdefault(
            '_organization_ownerships', dict())
        permissions = user.__dict__.setdefault(
            '_organization_permissions', dict())
        if ownerships.get(self.id) is None:
            qs = self.teams.filter(users=user)
            qs = qs.filter(Q(is_all_projects=True) | Q(projects=project))
            if qs.filter(is_owner_team=True).count():
                ownerships[self.id] = True
            else:
                permissions[self.id] = qs.values_list(
                    'permissions__slug', flat=True)

        if self.id in ownerships:
            return True
        if perm_slug in permissions.get(self.id, []):
            return True

        return False

    def __str__(self):
        return self.name


reversion.register(Organization, follow=['namespace_ptr'])

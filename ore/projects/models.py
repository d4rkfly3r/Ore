
from django.contrib.auth.models import AnonymousUser
from django.core import validators
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, F

from model_utils import Choices
from model_utils.fields import StatusField
from ore.core.models import Namespace
from ore.core.util import validate_not_prohibited, prefix_q, UserFilteringManager
from ore.core.regexs import EXTENDED_NAME_REGEX
import reversion


@reversion.register
class Project(models.Model):
    STATUS = Choices('active', 'deleted')
    status = StatusField()

    name = models.CharField('name', max_length=32,
                            validators=[
                                validators.RegexValidator(EXTENDED_NAME_REGEX, 'Enter a valid project name.',
                                                          'invalid'),
                                validate_not_prohibited,
                                ])
    namespace = models.ForeignKey(Namespace, related_name='projects')
    description = models.TextField('description')

    objects = UserFilteringManager()

    def get_absolute_url(self):
        return reverse('repo-projects-detail', kwargs={'namespace': self.namespace.name, 'project': self.name})

    @classmethod
    def is_visible_q(cls, prefix, user):
        if user.is_anonymous():
            return Namespace.is_visible_q(prefix + 'namespace__', user) & prefix_q(prefix, status='active')
        elif user.is_superuser:
            return Q()

        return Namespace.is_visible_q(prefix + 'namespace__', user) & (
            prefix_q(prefix, status='active') |
            cls.is_visible_if_hidden_q(prefix, user)
        )

    @staticmethod
    def is_visible_if_hidden_q(prefix, user):
        if user.is_anonymous():
            return Q()

        return ~prefix_q(prefix, status='deleted') & (
            (prefix_q(prefix, teams__users=user)) |
            (prefix_q(prefix, namespace__oreuser=user)) |
            (
                (
                    prefix_q(prefix, namespace__organization__teams__is_all_projects=True) |
                    prefix_q(prefix, namespace__organization__teams__projects__id=F('id'))
                ) &
                prefix_q(prefix, namespace__organization__teams__users=user)
            )
        )

    @property
    def full_name(self):
        return "{}/{}".format(self.namespace.name, self.name)

    def user_has_permission(self, user, perm_slug):
        if isinstance(user, AnonymousUser):
            return False
        elif user.is_superuser:
            return True

        ownerships = user.__dict__.setdefault('_project_ownerships', dict())
        permissions = user.__dict__.setdefault('_project_permissions', dict())
        if ownerships.get(self.id) is None and permissions.get(self.id) is None:
            qs = self.teams.filter(users=user)
            if qs.filter(is_owner_team=True).exists():
                ownerships[self.id] = True
                permissions[self.id] = []
            else:
                ownerships[self.id] = False
                permissions[self.id] = qs.values_list('permissions__slug', flat=True)

        if self.id in ownerships and ownerships[self.id]:
            return True
        if perm_slug in permissions.get(self.id, []):
            return True

        return Namespace.objects.get_subclass(id=self.namespace_id).user_has_permission(user, perm_slug, project=self)

    def __repr__(self):
        return '<Project %s by %s>' % (self.name, self.namespace.name)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('namespace', 'name')


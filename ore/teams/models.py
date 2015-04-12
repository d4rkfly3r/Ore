from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from ore.accounts.models import OreUser
from ore.core.models import Permission, Namespace, Organization
from django.core import validators
from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from ore.core.util import validate_not_prohibited, prefix_q, UserFilteringManager
from ore.projects.models import Project
from ore.core.regexs import EXTENDED_NAME_REGEX
import reversion


class Team(models.Model):
    name = models.CharField('name', max_length=80, null=False, blank=False,
                            validators=[
                                validators.RegexValidator(EXTENDED_NAME_REGEX, 'Enter a valid team name.', 'invalid'),
                                validate_not_prohibited,
                            ])
    users = models.ManyToManyField(OreUser, related_name='%(class)ss', blank=True)
    permissions = models.ManyToManyField(Permission, related_name='%(class)ss', blank=True)
    is_owner_team = models.BooleanField(default=False)

    def __repr__(self):
        props = ['owner'] if self.is_owner_team else []
        return '<Team %s [%s]>' % (self.name, ' '.join(props))

    def __str__(self):
        return self.name

    def check_consistent(self):
        return True

    def make_consistent(self):
        return

    class Meta:
        abstract = True


@reversion.register
class OrganizationTeam(Team):
    organization = models.ForeignKey(Organization, related_name='teams')
    projects = models.ManyToManyField(Project, related_name='organizationteams', blank=True)
    is_all_projects = models.BooleanField(default=False)

    objects = UserFilteringManager()

    def make_consistent(self):
        self.projects = self.projects.filter(namespace=self.organization)
        self.save()

    def check_consistent(self):
        return not self.projects.exclude(namespace=self.organization).exists()

    @staticmethod
    def is_visible_q(prefix, user):
        if user.is_anonymous():
            return prefix_q(prefix, id=-1)  # XXX: is there a better way of specifying "none"?
        elif user.is_superuser:
            return Q()

        return (
            prefix_q(prefix, organization=Organization.objects.filter(
                teams__users=user,
                teams__is_owner_team=True,
            )) |
            prefix_q(prefix, users=user)
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        props = (['all_projects'] if self.is_all_projects else []) + (['owner'] if self.is_owner_team else [])
        return '<OrganizationTeam %s in %s [%s]>' % (self.name, self.organization.name, ' '.join(props))

    class Meta:
        unique_together = ('organization', 'name')


@reversion.register
class ProjectTeam(Team):
    project = models.ForeignKey(Project, related_name='teams')

    def __str__(self):
        return self.name

    def __repr__(self):
        props = ['owner'] if self.is_owner_team else []
        return '<ProjectTeam %s in %s [%s]>' % (self.name, self.project.name, ' '.join(props))

    # TODO: we need to check here that if we're a user's project and we're the owner team, that that user is in us!

    class Meta:
        unique_together = ('project', 'name')

@receiver(post_save, sender=Project)
def create_project_owner_team(sender, instance, created, **kwargs):
    if instance and created:
        owning_namespace = Namespace.objects.get_subclass(id=instance.namespace_id)
        if isinstance(owning_namespace, OreUser):
            team = ProjectTeam.objects.create(
                project=instance,
                is_owner_team=True,
                name='Owners',
                )
            team.users = [owning_namespace]
            team.save()

@receiver(post_save, sender=Organization)
def create_organization_owner_team(sender, instance, created, **kwargs):
    if instance and created:
        OrganizationTeam.objects.create(
            name='Owners',
            organization=instance,
            is_all_projects=True,
            is_owner_team=True,
            )

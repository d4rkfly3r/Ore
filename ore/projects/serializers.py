from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ore.core.field_security_policy import FieldSecurityPolicyMixin, FieldSecurityPolicy
from ore.core.models import Namespace

from ore.projects.models import Project


def project_allowed_namespace_queryset_generator(user, obj, field):
    if user.is_authenticated():
        if not user.is_superuser:
            namespace_filter = (
                Q(organization__teams__users=user, organization__teams__is_owner_team=True,) |
                Q(organization__teams__users=user, organization__teams__permissions__slug='project.create',) |
                Q(oreuser=user)
            )
            namespace_filter = namespace_filter | Q(id=obj.namespace_id)
            return Namespace.objects.filter(namespace_filter)
        else:
            return Namespace.objects.all()
    else:
        return Namespace.objects.none()


class ProjectSerializer(FieldSecurityPolicyMixin, ModelSerializer):
    namespace = serializers.HyperlinkedRelatedField(
        queryset=Namespace.objects.all(),
        view_name='namespace-detail',
        lookup_field='name',
    )
    full_name = serializers.CharField(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='project-detail',
        lookup_field='full_name',
        lookup_url_kwarg='name',
    )

    policy = {
        'namespace': [
            FieldSecurityPolicy.AllowWriteIf(FieldSecurityPolicy.Permission('project.transfer')),
            FieldSecurityPolicy.SetQuerySet(project_allowed_namespace_queryset_generator),
        ],
        'name': FieldSecurityPolicy.AllowWriteIf(FieldSecurityPolicy.Permission('project.rename')),
        'description': FieldSecurityPolicy.AllowWriteIf(FieldSecurityPolicy.Permission('project.edit')),
    }

    class Meta:
        model = Project
        fields = ['url', 'full_name', 'name', 'namespace', 'description']
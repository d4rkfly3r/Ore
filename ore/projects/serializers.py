from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ore.core.models import Namespace

from ore.projects.models import Project


class ProjectSerializer(ModelSerializer):
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

    def get_fields(self):
        fields = super(ProjectSerializer, self).get_fields()
        user = self.context['request'].user

        # Restrict namespaces to those which this user can put projects under
        instance = getattr(self, 'instance', None)
        if user.is_authenticated():
            if not user.is_superuser:
                namespace_filter = (
                    Q(organization__teams__users=user, organization__teams__is_owner_team=True,) |
                    Q(organization__teams__users=user, organization__teams__permissions__slug='project.create',) |
                    Q(oreuser=user)
                )
                if instance and getattr(instance, 'namespace', None):
                    namespace_filter = namespace_filter | Q(id=instance.namespace_id)
                fields['namespace'].queryset = Namespace.objects.filter(namespace_filter)
        else:
            fields['namespace'].queryset = Namespace.objects.none()

        if instance and getattr(instance, 'user_has_permission', None):
            # work out which fields should be immutable:
            permissions_required = {
                'namespace': ['project.transfer'],
                'name': ['project.rename'],
                'description': ['project.edit'],
            }
            for _, field in fields.items():
                field.read_only = True  # default all fields to read-only unless set otherwise

            for field_name, permissions in permissions_required.items():
                if all([self.instance.user_has_permission(user, p) for p in permissions]):
                    fields[field_name].read_only = False  # and then enable the fields that should be writable

        return fields

    class Meta:
        model = Project
        fields = ['url', 'full_name', 'name', 'namespace', 'description']
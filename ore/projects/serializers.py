from django.db.models import Q
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ore.core.field_security_policy import FieldSecurityPolicySerializerMixin, FieldSecurityPolicy
from ore.core.models import Namespace

from ore.projects.models import Project


class ProjectSerializer(FieldSecurityPolicySerializerMixin, ModelSerializer):
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

    class Meta:
        model = Project
        fields = ['url', 'full_name', 'name', 'namespace', 'description']
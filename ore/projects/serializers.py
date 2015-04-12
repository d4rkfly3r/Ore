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
    full_name = serializers.CharField()
    url = serializers.HyperlinkedIdentityField(
        view_name='project-detail',
        lookup_field='full_name',
        lookup_url_kwarg='name',
    )

    class Meta:
        model = Project
        fields = ['url', 'name', 'namespace', 'description', 'full_name']
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from ore.accounts.models import OreUser
from ore.core.models import Permission, Organization
from ore.teams.models import Team, OrganizationTeam


class TeamSerializer(ModelSerializer):
    users = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=OreUser.objects.all(),
        view_name='user-detail',
        lookup_field='name',
    )
    permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Permission.objects.all(),
    )

    class Meta:
        model = Team
        read_only_fields = ['is_owner_team']
        fields = read_only_fields + ['name', 'users', 'permissions']


class OrganizationTeamSerializer(TeamSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='organization-team-detail')
    organization = serializers.HyperlinkedRelatedField(
        queryset=Organization.objects.all(),
        view_name='organization-detail',
        lookup_field='name',
    )

    class Meta(TeamSerializer.Meta):
        model = OrganizationTeam
        read_only_fields = TeamSerializer.Meta.read_only_fields + ['is_all_projects', 'url']
        fields = read_only_fields + ['name', 'organization', 'users', 'permissions', 'projects']

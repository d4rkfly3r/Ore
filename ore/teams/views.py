from django.contrib.auth.models import AnonymousUser
from rest_framework.viewsets import ModelViewSet
from ore.core.models import Organization
from ore.teams.models import OrganizationTeam
from ore.teams.permissions import OrganizationTeamPermission
from ore.teams.serializers import TeamSerializer, OrganizationTeamSerializer


class TeamViewSet(ModelViewSet):

    lookup_field = 'pk'
    serializer_class = TeamSerializer
    permission_classes = [OrganizationTeamPermission]


class OrganizationTeamViewSet(TeamViewSet):

    serializer_class = OrganizationTeamSerializer

    def get_queryset(self):
        return OrganizationTeam.objects.as_user(self.request.user)

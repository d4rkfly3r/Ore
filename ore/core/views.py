from django.views.generic.base import TemplateView
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from ore.api.permissions import OrePermission
from ore.teams.models import OrganizationTeam
from ore.teams.serializers import OrganizationTeamSerializer

from .serializers import NamespaceSerializer, OrganizationSerializer
from .models import Namespace, Organization


class AppView(TemplateView):

    template_name = 'app.html'


class NamespaceViewSet(ReadOnlyModelViewSet):

    lookup_field = 'name'
    serializer_class = NamespaceSerializer

    def get_queryset(self):
        return Namespace.objects.as_user(self.request.user).select_subclasses()


class OrganizationViewSet(ModelViewSet):

    lookup_field = 'name'
    serializer_class = OrganizationSerializer
    permission_classes = [OrePermission]

    def get_queryset(self):
        return Organization.objects.as_user(self.request.user)

    def perform_create(self, serializer):
        super(OrganizationViewSet, self).perform_create(serializer)
        if self.request.user.is_authenticated():
            instance = serializer.instance
            owner_team = OrganizationTeam.objects.get(organization=instance, is_owner_team=True)
            owner_team.users.add(self.request.user)

    @detail_route(methods=['GET'])
    def teams(self, request, name=None):
        instance = self.get_object()
        serializer = OrganizationTeamSerializer(
            instance.teams.all(),
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)
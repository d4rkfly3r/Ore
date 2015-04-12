from django.views.generic.base import TemplateView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

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

    def get_queryset(self):
        return Organization.objects.as_user(self.request.user)
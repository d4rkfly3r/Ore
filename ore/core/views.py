from django.views.generic.base import TemplateView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import NamespaceSerializer
from .models import Namespace


class AppView(TemplateView):

    template_name = 'app.html'


class NamespaceViewSet(ReadOnlyModelViewSet):

    lookup_field = 'name'
    serializer_class = NamespaceSerializer

    def get_queryset(self):
        return Namespace.objects.as_user(self.request.user).select_subclasses()
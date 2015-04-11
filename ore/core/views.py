from django.views.generic.base import TemplateView
from rest_framework.viewsets import ModelViewSet

from .serializers import NamespaceSerializer
from .models import Namespace


class AppView(TemplateView):

    template_name = 'app.html'


class NamespaceViewSet(ModelViewSet):

    serializer_class = NamespaceSerializer

    def get_queryset(self):
        return Namespace.objects.as_user(self.request.user).all()

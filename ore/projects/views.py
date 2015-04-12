from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from ore.core.regexs import REPO_URL_REGEX
from ore.projects.models import Project
from ore.projects.serializers import ProjectSerializer


class ProjectViewSet(ModelViewSet):

    lookup_field = 'name'
    lookup_value_regex = REPO_URL_REGEX
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.as_user(self.request.user)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        namespace, _, name = self.kwargs['name'].partition('/')
        obj = get_object_or_404(queryset, namespace__name=namespace, name=name)

        self.check_object_permissions(self.request, obj)

        return obj
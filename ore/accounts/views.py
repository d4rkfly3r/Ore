from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from ore.accounts.models import OreUser
from ore.accounts.permissions import UserPermission
from ore.accounts.serializers import UserSerializer, UserFullSerializer


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):

    lookup_field = 'name'
    permission_classes = [UserPermission]

    def get_queryset(self):
        return OreUser.objects.as_user(self.request.user)

    def get_serializer(self, instance=None, *args, **kwargs):
        serializer_class = UserSerializer

        if instance and instance == self.request.user:
            serializer_class = UserFullSerializer

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(instance=instance, *args, **kwargs)

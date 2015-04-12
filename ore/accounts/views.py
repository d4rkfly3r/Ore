from django.contrib.auth import logout, authenticate, login
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from rest_framework import mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet
from ore.accounts.models import OreUser
from ore.accounts.serializers import UserSerializer, UserFullSerializer


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):

    lookup_field = 'name'

    def get_queryset(self):
        return OreUser.objects.as_user(self.request.user)

    def get_serializer(self, instance=None, *args, **kwargs):
        serializer_class = UserSerializer

        if (instance is not None and
            not isinstance(instance, QuerySet) and
            instance.user_has_permission(self.request.user, 'edit')):
            serializer_class = UserFullSerializer

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(instance=instance, *args, **kwargs)


# TODO: ratelimiting on authentication attempts - note that Django Rest Framework also provides authentication!
@api_view(['GET', 'POST', 'DELETE'])
def current_session(request, format=None):
    if request.user.is_authenticated() and request.method == 'DELETE':
        # logout
        logout(request)
        return Response(None, status=204)
    elif not request.user.is_authenticated() and request.method == 'POST':
        # log in
        if 'username' not in request.data or 'password' not in request.data:
            return Response({'detail': '"username" and "password" must both be provided.'}, status=400)

        un, pw = request.data['username'], request.data['password']
        user = authenticate(username=un, password=pw)
        if user is not None and user.status != 'active':
            return Response({'detail': 'Account disabled.'}, status=401)
        elif user is None:
            if OreUser.objects.filter(name=un).exists():
                return Response({'detail': 'Password incorrect.'}, status=401)
            else:
                return Response({'detail': 'Account does not exist.'}, status=404)

        assert user is not None and user.status == 'active'

        login(request, user)

    user_url = None
    if request.user.is_authenticated():
        user_url = reverse('user-detail', request=request, kwargs={'name': request.user.name})

    return Response({
        'user': user_url,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
    })

@api_view(['GET'])
def current_session_user(request, format=None):
    if not request.user.is_authenticated():
        return Response({'detail': 'Not logged in!'}, status=404)

    return HttpResponseRedirect(reverse('user-detail', request=request, kwargs={'name': request.user.name}))
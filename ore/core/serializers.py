from django.db.models import QuerySet
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.reverse import reverse

from ore.accounts.models import OreUser
from ore.core.models import Namespace, Organization


class NamespaceSerializer(ModelSerializer):
    type = SerializerMethodField()
    url = SerializerMethodField()

    def get_type(self, obj):
        if isinstance(obj, OreUser):
            return 'user'
        elif isinstance(obj, Organization):
            return 'organization'
        raise Exception('unknown type %s' % (type(obj),))

    def get_url(self, obj):
        return reverse(self.get_type(obj) + '-detail',
            kwargs=dict(
                name=obj.name,
            ),
           request=self._context['request'],
           format=self._context['format'],
        )

    class Meta:
        model = Namespace
        read_only_fields = ['name', 'status', 'type', 'url', 'avatar']
        fields = read_only_fields


class OrganizationSerializer(NamespaceSerializer):
    avatar = SerializerMethodField()

    def get_avatar(self, obj):
        return obj.get_avatar(self.context['request'])

    class Meta(NamespaceSerializer.Meta):
        model = Organization
        read_only_fields = NamespaceSerializer.Meta.read_only_fields
        read_only_fields.remove('name')

        fields = read_only_fields + ['name', 'avatar_image']
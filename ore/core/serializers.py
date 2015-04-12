from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.reverse import reverse

from ore.accounts.models import OreUser
from ore.core.models import Namespace, Organization


class NamespaceSerializer(ModelSerializer):
    type = SerializerMethodField()
    full_url = SerializerMethodField()

    def get_type(self, obj):
        if isinstance(obj, OreUser):
            return 'user'
        elif isinstance(obj, Organization):
            return 'organization'
        raise Exception('unknown type %s' % (type(obj),))

    def get_full_url(self, obj):
        return reverse(self.get_type(obj) + '-detail',
            kwargs=dict(
                name=obj.name,
            ),
           request=self._context['request'],
           format=self._context['format'],
        )

    class Meta:
        model = Namespace
        fields = ['status', 'name', 'type', 'full_url', 'avatar']
        read_only_fields = ['name', 'status', 'type', 'full_url', 'avatar']


class OrganizationSerializer(NamespaceSerializer):
    class Meta(NamespaceSerializer.Meta):
        model = Organization
        read_only_fields = ['status', 'type', 'full_url', 'avatar']
        fields = read_only_fields + ['name', 'avatar_image']
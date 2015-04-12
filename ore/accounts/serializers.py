from ore.accounts.models import OreUser
from ore.core.serializers import NamespaceSerializer


class UserSerializer(NamespaceSerializer):

    def create(self, validated_data):
        # no.
        raise ValueError("This shouldn't be called")

    class Meta(NamespaceSerializer.Meta):
        model = OreUser
        fields = NamespaceSerializer.Meta.fields + ['date_joined']
        read_only_fields = fields


class UserFullSerializer(UserSerializer):

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))

        return super(UserFullSerializer, self).update(instance, validated_data)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['password']
        extra_kwargs = {'password': {'write_only': True}}

from rest_framework.serializers import ModelSerializer
from ore.core.models import Namespace


class NamespaceSerializer(ModelSerializer):

    class Meta:
        model = Namespace

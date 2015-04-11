from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns
from ore.core.views import NamespaceViewSet

router = SimpleRouter()
router.register(r'namespaces', NamespaceViewSet, base_name='Namespace')

urlpatterns = format_suffix_patterns(router.urls, allowed=['json', 'html'])

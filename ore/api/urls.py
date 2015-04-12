from rest_framework.routers import DefaultRouter
from ore.accounts.views import UserViewSet
from ore.core.views import NamespaceViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'namespaces', NamespaceViewSet, base_name='namespace')
router.register(r'users', UserViewSet, base_name='user')

urlpatterns = router.urls

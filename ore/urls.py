from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
import grappelli.urls
from ore.core.views import AppView

urlpatterns = patterns(
    '',

    url(r'^grappelli/', include(grappelli.urls)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', AppView.as_view()),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

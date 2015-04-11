from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
import grappelli.urls

import ore.api.urls
import ore.core.urls
import ore.accounts.urls
from ore.core.views import AppView
import ore.projects.urls
import ore.versions.urls
import ore.teams.urls

urlpatterns = patterns(
    '',

    url(r'^grappelli/', include(grappelli.urls)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(ore.api.urls)),

    url(r'.*', AppView.as_view()),

    url(r'', include(ore.accounts.urls)),
    url(r'', include(ore.core.urls)),
    url(r'', include(ore.projects.urls)),

    url(r'', include(ore.versions.urls)),
    url(r'', include(ore.teams.urls))

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

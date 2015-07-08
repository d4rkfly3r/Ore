from django.conf.urls import patterns, url, include
from django.conf import settings
from django.views.generic import RedirectView
from ore.accounts import views

accounts_urlpatterns = patterns(
    '',
    url(r'^logout/$', views.LogoutView.as_view(),
        name='accounts-logout'),
)

if not settings.DISCOURSE_SSO_ENABLED:
    accounts_urlpatterns += patterns('',
        url(r'^login/$', views.loginview,
            name='accounts-login'),
        url(r'^new/$', views.RegisterView.as_view(),
            name='accounts-register'),
    )
else:
    sso_redirect_view = RedirectView.as_view(pattern_name='sso-begin', permanent=False, query_string=True)
    accounts_urlpatterns += patterns('',
        url(r'^login/$', sso_redirect_view,
            name='accounts-login'),
        url(r'^new/$', sso_redirect_view,
            name='accounts-register'),
    )
    

urlpatterns = patterns(
    '',
    url(r'^accounts/', include(accounts_urlpatterns)),
    url(r'^settings/', include(patterns('',
                                        url(r'^$', RedirectView.as_view(
                                            pattern_name='settings-profile', permanent=True), name='settings-root' ),
                                        url(r'^profile/$', views.ProfileSettings.as_view(),
                                            name='settings-profile'),
                                        ))),
)

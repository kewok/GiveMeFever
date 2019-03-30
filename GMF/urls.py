"""GMF URL Configuration
"""

from django.conf.urls import url,include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('IntroApp.urls')),
    url(r'^SetupEpidemic/', include('SetupEpidemic.urls')),
    url(r'^JoinEpidemic/', include('JoinEpidemic.urls')),
    url(r'^CheckStatus/', include('CheckStatus.urls')),
    url(r'^DownloadEpidemic/', include('DownloadEpidemic.urls')),
]

urlpatterns += staticfiles_urlpatterns()

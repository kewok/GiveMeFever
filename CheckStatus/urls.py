from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.check_status, name='check_status'),
    url(r'^SelectIntervention/$', views.select_intervention, name='select_intervention'),
    url(r'^ShowHistory/$', views.show_history, name='show_history'),
    url(r'^StartOver/$', views.start_over, name='start_over'),
	]

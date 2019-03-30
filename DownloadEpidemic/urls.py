from django.conf.urls import url, include
from django.views.generic import ListView, DetailView,TemplateView

from . import views

urlpatterns = [
	url(r'^$', views.find_epidemic, name='find_epidemic'),
	url(r'^download/$', views.download_epidemic, name='download_epidemic'),
	]

from django.conf.urls import url, include
from django.views.generic import ListView, DetailView,TemplateView

from . import views

urlpatterns = [
    url(r'^$', views.pathogen_chooser, name='choose_pathogens'),
    url(r'^neoForma/$', views.customize_pathogen, name='customize_pathogen'),
    url(r'^ChooseCompartment/$',views.compartment_chooser, name='choose_compartment'),
    url(r'^SI/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^SIS/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^SIR/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^SEIR/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^SEIS/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^SEIRS/$', views.customize_compartment_model, name='customize_compartment_model'),
    url(r'^TransmissionSelection/$', views.submit_compartment, name='submit_compartment'),
    url(r'^FD/$', views.customize_FD_transmission, name='customize_FD_transmission'),
    url(r'^InterventionSetup/$', views.submit_transmission, name='submit_transmission'),
    url(r'^finalize/$', views.submit_intervention, name='submit_intervention'),
    url(r'^finalize_settings/$', views.finalize_settings, name='finalize_settings'),
    url(r'^finish/$', views.finish_setup, name='finish_setup'),
    url(r'^StartOver/$', views.start_over, name='start_over'),
	]

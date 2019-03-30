# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.urls import reverse
import decimal

from .models import PathogenSettings, EpidemicSettings, InterventionSettings
from .forms import PathogenForm, InterventionForm, EpidemicInitializationForm


def pathogen_chooser(request):
	return render(request, 'SetupEpidemic/pathogen_setup.html')

def customize_pathogen(request):
	if request.method == 'POST':
		return render(request, 'SetupEpidemic/compartment_setup.html')
	if request.method == 'GET':
		return render(request, 'SetupEpidemic/includes/partial_pathogen_create.html')
	
def compartment_chooser(request):
	return render(request, 'SetupEpidemic/compartment_setup.html')

def customize_compartment_model(request):
	if request.method == 'GET':
		return render(request, 'SetupEpidemic/includes/partial_' + request.GET.get('compartment_model','') + '_model_create.html')
	if request.method == 'POST':
		return render(request, 'SetupEpidemic/transmission_setup.html')

def submit_compartment(request):
	return render(request, 'SetupEpidemic/transmission_setup.html')

def submit_transmission(request):
	return render(request, 'SetupEpidemic/intervention_setup.html')

def customize_FD_transmission(request):
	return render(request, 'SetupEpidemic/includes/partial_FD_create.html')

def submit_intervention(request):
	return redirect('finalize_settings')

def finalize_settings(request):
	if request.method == 'GET':
		epidemic_initialization_form = EpidemicInitializationForm()
	return render(request, 'SetupEpidemic/finalize.html', context = {'epidemic_initialization_form': epidemic_initialization_form})

def finish_setup(request):
	if request.method == 'POST':
		epidemic_initialization_form = EpidemicInitializationForm(request.POST)
		if epidemic_initialization_form.is_valid():
			epidemic_initialization_form.finalize()
			epidemic_initialization_form.save()
			return HttpResponseRedirect('/')
		else:
			print('Errors of form ' + str(epidemic_initialization_form.errors))
		return render(request, 'SetupEpidemic/finalize.html', context = {'epidemic_initialization_form': epidemic_initialization_form})


def start_over(request):
	return HttpResponseRedirect('/')
	


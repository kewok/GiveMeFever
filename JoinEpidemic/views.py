# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from .forms import HostForm
from GMF.models import Epidemic, Host, Compartment

def find_epidemic(request):
	if request.method == 'GET':
		host_form = HostForm()
	return render(request, 'JoinEpidemic/find_epidemic.html', context = {'host_form': host_form})

def join_epidemic(request):
	if request.method == 'POST':
		host_form = HostForm(request.POST)
		if host_form.is_valid():
			current_epidemic = Epidemic.objects.get(name = host_form.get_epidemic_name())
			if Host.objects.filter(epidemic__name=host_form.get_epidemic_name(), name=str(host_form)).exists():
				current_host = Host.objects.get(name=str(host_form), epidemic=current_epidemic)
			else:
				current_host = Host.objects.create(name=str(host_form), epidemic=current_epidemic, current_compartment=Compartment.objects.get(name='S', epidemic=current_epidemic))
				host_form.instance.host = current_host
				host_form.save()
			request.session['host_name'] = current_host.name
			request.session['last_joined_epidemic'] = current_epidemic.name
			return redirect('/CheckStatus') 
		else:
			print('Errors of form ' + str(host_form.errors))
	return render(request, 'JoinEpidemic/find_epidemic.html', context = {'host_form': host_form})

from __future__ import unicode_literals
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from GMF.models import Epidemic, Host, Compartment, CompartmentChange
from SetupEpidemic.models import EpidemicSettings, InterventionSettings

import pytz
from django.utils import timezone

# from https://stackoverflow.com/a/32584886
def convert_to_localtime(utctime):
	fmt = '%d/%m/%Y %H:%M'
	utc = utctime.replace(tzinfo=pytz.UTC)
	local_time = utc.astimezone(timezone.get_current_timezone())
	return local_time.strftime(fmt)

def check_status(request):
	if request.session.get('last_joined_epidemic') is None or request.session.get('host_name') is None:
		return redirect('/JoinEpidemic')
	else:
		epidemic = Epidemic.objects.get(name=request.session.get('last_joined_epidemic'))
		try:
			host = Host.objects.get(name=request.session.get('host_name'), epidemic=epidemic)
			epidemic_settings = EpidemicSettings.objects.get(epidemic=epidemic)
			# Find the host's compartment among the EpidemicCompartments associated with this epidemic and this host.
			host_compartment = host.current_compartment
			if host_compartment.name=='Es' or host_compartment.name=='Is':
				template = determine_sick_host_template(epidemic_settings)
				return render(request, template, context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='S' or host_compartment.name=='Ea' or host_compartment.name=='Ia' or host_compartment.name=='R':
				template = determine_not_sick_host_template(epidemic_settings)
				return render(request, template, context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='D':
				return render(request, 'CheckStatus/dead.html', context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='V':
				return render(request, 'CheckStatus/vaccinated.html', context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='M':
				return render(request, 'CheckStatus/medicated.html', context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='K':
				return render(request, 'CheckStatus/isolated.html', context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
			if host_compartment.name=='Q':
				return render(request, 'CheckStatus/quarantined.html', context = {'epidemic_name': epidemic_settings.name,'host_compartment': host_compartment})
		except Exception as e: 
			print(e)
			return redirect('/JoinEpidemic')
		


def determine_not_sick_host_template(epidemic_settings):
	if epidemic_settings.intervention_available('Q'):
		if epidemic_settings.intervention_available('V') and epidemic_settings.intervention_available('B'):
			return 'CheckStatus/NotSick/quarantine_or_vaccinate_or_block.html'
		if epidemic_settings.intervention_available('V') and not epidemic_settings.intervention_available('B'):
			return 'CheckStatus/NotSick/quarantine_or vaccinate.html'
		if epidemic_settings.intervention_available('B') and not epidemic_settings.intervention_available('V'):
			return 'CheckStatus/NotSick/quarantine_or_block.html'
		if not epidemic_settings.intervention_available('B') and not epidemic_settings.intervention_available('V'):
			return 'CheckStatus/NotSick/quarantine_only.html'
	else:
		if epidemic_settings.intervention_available('V') and epidemic_settings.intervention_available('B'):
			return 'CheckStatus/NotSick/vaccinate_or_block.html'
		if epidemic_settings.intervention_available('V') and not epidemic_settings.intervention_available('B'):
			return 'CheckStatus/NotSick/vaccinate_only.html'
		if epidemic_settings.intervention_available('B') and not epidemic_settings.intervention_available('V'):
			return 'CheckStatus/NotSick/block_only.html'
		if not epidemic_settings.intervention_available('B') and not epidemic_settings.intervention_available('V'):
			return 'CheckStatus/NotSick/await_infection.html'

def determine_sick_host_template(epidemic_settings):
	if epidemic_settings.intervention_available('K'):
		if epidemic_settings.intervention_available('Q') and epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/isolate_or_quarantine_or_medicate.html'
		if epidemic_settings.intervention_available('Q') and not epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/isolate_or_quarantine.html'
		if not epidemic_settings.intervention_available('Q') and  epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/isolate_or_medicate.html'
		if not epidemic_settings.intervention_available('Q') and not epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/isolate_only.html'
	else:
		if epidemic_settings.intervention_available('Q') and epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/quarantine_or_medicate.html'
		if epidemic_settings.intervention_available('Q') and not epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/quarantine_only.html'
		if not epidemic_settings.intervention_available('Q') and epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/medicate_only.html'
		if not epidemic_settings.intervention_available('Q') and not epidemic_settings.intervention_available('M'):
			return 'CheckStatus/Sick/await_recovery.html'

def select_intervention(request):
	epidemic = Epidemic.objects.get(name=request.session.get('last_joined_epidemic'))
	host = Host.objects.get(name=request.session.get('host_name'), epidemic=epidemic)
	intervention_settings = InterventionSettings.objects.get(epidemic_settings=EpidemicSettings.objects.get(epidemic=epidemic))
	intervention_chosen=str(request.GET.get('intervention',''))
	if intervention_chosen=='B':
		if host.transmission_modifier == 1: # ensures that blocking transmission only works once.
			host.transmission_modifier = host.transmission_modifier * intervention_settings.transmission_blocking
			host.save()
	else:
		# Get the compartment to which the host will belong after the intervention
		new_compartment = Compartment.objects.get(epidemic=epidemic, name=intervention_chosen)
		# Add the host to the compartment to which it will belong after the intervention
		CompartmentChange.objects.create(epidemic=epidemic, host=host, source_compartment=host.current_compartment, destination_compartment=new_compartment, time_switched=timezone.datetime.today())
		host.current_compartment = new_compartment
		host.save()
	return HttpResponseRedirect('/')

def show_history(request):
	epidemic = Epidemic.objects.get(name=request.session.get('last_joined_epidemic'))
	host = Host.objects.get(name=request.session.get('host_name'), epidemic=epidemic)
	health_history = CompartmentChange.objects.filter(host=host)
	status = []
	COMPARTMENTS = {'S':'Not sick', 'Ea':'Not sick','Ia':'Not sick','R':'Not sick','Es':'Sick','Is':'Sick','D':'Dead','V':'Vaccinated','M':'Medicated', 'K':'Isolated', 'Q':'Quarantined'}
	for value in health_history:
		status.append(tuple((convert_to_localtime(value.time_switched), COMPARTMENTS[value.source_compartment.name], COMPARTMENTS[value.destination_compartment.name])))
	return render(request, 'CheckStatus/show_history.html', context = {'host_name': host.name , 'status': status})

def start_over(request):
	return HttpResponseRedirect('/')


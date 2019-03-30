# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from .forms import EpidemicForm
from GMF.models import Epidemic, Host, Compartment, InfectionEvent, CompartmentChange
from SetupEpidemic.models import EpidemicSettings, PathogenSettings, InterventionSettings

import json
import decimal
import datetime
from dateutil import tz
# Magic to enable json enconding of Decimal object: from https://stackoverflow.com/a/3885198
class customEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			return float(o)
		if isinstance(o, datetime.datetime):
			return o.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%S.%f%Z')
		return super(customEncoder, self).default(o)


def find_epidemic(request):
	if request.method == 'GET':
		epidemic_form = EpidemicForm()
	return render(request, 'DownloadEpidemic/find_epidemic.html', context = {'epidemic_form': epidemic_form})

def download_epidemic(request):
	if request.method == 'POST':
		epidemic_form = EpidemicForm(request.POST)
		if epidemic_form.is_valid():
			current_epidemic = Epidemic.objects.get(name = epidemic_form.get_disease_name())
			from django.forms.models import model_to_dict
			epi_dict = EpidemicSettings.objects.get(name = epidemic_form.get_disease_name()).__dict__.copy()
			epi_dict['hosts'] = [entry.name for entry in Host.objects.filter(epidemic=current_epidemic).all()]
			epi_dict['steps_iterated'] = current_epidemic.steps_iterated
			epi_dict['transmission_rate'] = current_epidemic.transmission_rate
			epi_dict['intervention_settings'] = InterventionSettings.objects.get(epidemic_settings=EpidemicSettings.objects.get(name = epidemic_form.get_disease_name())).__dict__.copy()
			epi_dict['pathogen_settings'] = PathogenSettings.objects.get(epidemic_settings=EpidemicSettings.objects.get(name = epidemic_form.get_disease_name())).__dict__.copy()


			# Remove extraneous, django-specific entries"
			for key in list(epi_dict.keys()):
				if key.startswith('_'):
					epi_dict.pop(key,None)
			# From https://stackoverflow.com/a/14962509
			def _delete_key(obj, key):
				for k, v in obj.items():
					if isinstance(v,dict):
						v.pop(key, None)
				if key in obj: obj.pop(key,None)
			_delete_key(epi_dict,'random_key')
			_delete_key(epi_dict,'id')
			_delete_key(epi_dict,'_state')
			epi_dict.pop('temp_password',None)
			epi_dict.pop('intervention_settings_id',None)
			epi_dict.pop('pathogen_settings_id',None)

			compartments = [{entry['name']:entry['transition_rates']} for entry in Compartment.objects.filter(epidemic=current_epidemic).values()]

			try: 
				InfectionEvent.objects.filter(epidemic=current_epidemic).exists()
				infection_network = InfectionEvent.objects.filter(epidemic=current_epidemic).values()
				infections = [entry for entry in infection_network]
				epi_net = {}
				k=1
				for infection_event in infections:
					if infection_event['source_host_id']:
						epi_net[k] = {'infection_date': infection_event['date_infected'], 'source_host': Host.objects.get(id=infection_event['source_host_id']).name, 'infected_host': Host.objects.get(id=infection_event['host_infected_id']).name, 'infections_attempted': infection_event['secondary_infections_attempted'], 'infections_succeeded': infection_event['secondary_infections_succeeded']}
					else:
						epi_net[k] = {'infection_date': infection_event['date_infected'], 'infected_host': Host.objects.get(id=infection_event['host_infected_id']).name, 'infections_attempted': infection_event['secondary_infections_attempted'], 'infections_succeeded': infection_event['secondary_infections_succeeded']}
					k = k + 1
			except Exception as e: 
				print(e)
				epi_net=None
			try:
				CompartmentChange.objects.filter(epidemic=current_epidemic).exists()
				host_histories = CompartmentChange.objects.filter(epidemic=current_epidemic).values()
				changes = [entry for entry in host_histories]
				change_dict = {}
				k=1
				for change_event in changes:
					change_dict[k] = {'host': Host.objects.get(id=change_event['host_id']).name, 'source_compartment': Compartment.objects.get(id=change_event['source_compartment_id']).name,'destination_compartment':Compartment.objects.get(id=change_event['destination_compartment_id']).name,'switch_time':change_event['time_switched']}
					k=k+1
			except:
				change_dict=None
			epidemic_data = json.dumps({'epidemic_properties': epi_dict, 'epidemic_network': epi_net, 'host_histories': change_dict, 'compartments':compartments}, cls=customEncoder)
			response = HttpResponse(str(epidemic_data), content_type='text/plain')
			response['Content-Disposition'] = 'attachment; filename=' + str(current_epidemic.name) + '.json'
			return response
		else:
			print('Errors of form ' + str(epidemic_form.errors))
	return render(request, 'DownloadEpidemic/find_epidemic.html', context = {'epidemic_form': epidemic_form})


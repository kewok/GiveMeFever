# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import numpy as np
from math import exp
import os
import copy
import random

from .models import Host, Compartment, EpidemicSettings, PathogenSettings, InfectionEvent, CompartmentChange
import json
import decimal
from django.utils import timezone

import pytz
utc=pytz.UTC

class TransmissionEvent:
	def __init__(self, epidemic):
		self.susceptibles = Host.objects.filter(epidemic=epidemic, current_compartment__name='S').all()
		self.original_infectious = Host.objects.filter(epidemic=epidemic, current_compartment__name__in= ('Ia','Is')).all()
		self.epidemic = epidemic
		self.epidemic_settings = EpidemicSettings.objects.get(epidemic=epidemic)
	
	def simulate_transmission(self):
		transmission_functions = {'DD': self.simulate_density_dependent_transmission, 'FD': self.simulate_frequency_dependent_transmission}
		transmission_functions[self.epidemic_settings.transmission_mode]()
	
	def simulate_density_dependent_transmission(self):		
		"""Iterate over the list of infectious hosts and determine whether there will be an infection event betweem the focal infectious host and a given susceptible host, conditioned on a contact event. Note the number of contact events should increase as the number of susceptibles increase."""
		for host_I in self.original_infectious:
			number_of_contacts = len(self.suscpetibles)
			#InfectionEvent.objects.filter(host_infected=host_I).order_by('-id')[0].secondary_infections_attempted += number_of_contacts
			IE=InfectionEvent.objects.filter(host_infected=host_I).latest('date_infected')
			IE.secondary_infections_attempted += number_of_contacts
			IE.save()
			for host_S in self.susceptibles:
				self.simulate_infection(host_S, host_I)
			self.susceptibles = Host.objects.filter(epidemic=self.epidemic, current_compartment__name='S').all()

					
	def simulate_frequency_dependent_transmission(self):	
		"""Actually it's not quite clear to me this is different from the routine old_simulate_density_dependent_transmission. Iterate over the list of encountered hosts and determine whether there will be a contact event betwee the focal infectious host and a susceptible host. If there is a contact event and the host is a susceptible individual, determine if there would be an infection event."""
		for host_I in self.original_infectious:
			number_of_contacts = min(np.random.poisson(self.epidemic_settings.hosts_encountered, size=1)[0], len(self.susceptibles))
			#InfectionEvent.objects.filter(host_infected=host_I).order_by('-id')[0].secondary_infections_attempted += number_of_contacts
			IE=InfectionEvent.objects.filter(host_infected=host_I).latest('date_infected')
			IE.secondary_infections_attempted += number_of_contacts
			IE.save()
			for i in range(0, number_of_contacts):
				if len(self.susceptibles):
					host_S = random.choice(self.susceptibles)
					self.simulate_infection(host_S, host_I)
					self.susceptibles = Host.objects.filter(epidemic=self.epidemic, current_compartment__name='S').all()
					

	def simulate_infection(self, host_S, host_I):
		""" Determine whether there will be a bernoulli probability controlled infection event. For now, this depends only on the susceptible host, but presumably subsequent iterations could incorporate a GPS-based location neighborhood or an evolving pathogen where this depends on the infecting host as well. """
		baseline_infection_rate = decimal.Decimal(self.epidemic.transmission_rate)
		if np.random.binomial(1, host_S.transmission_modifier * baseline_infection_rate):
			if 'Ea' in list(self.epidemic_settings.compartmental_model) or 'Es' in list(self.epidemic_settings.compartmental_model): # if we have incubation period
				if np.random.binomial(1, PathogenSettings.objects.get(epidemic_settings=self.epidemic_settings).percent_symptomatic):
					host_S.current_compartment = Compartment.objects.get(epidemic=self.epidemic, name='Es')
				else:
					host_S.current_compartment = Compartment.objects.get(epidemic=self.epidemic, name='Ea')
			else: # if straight to infectious
				if np.random.binomial(1, PathogenSettings.objects.get(epidemic_settings=self.epidemic_settings).percent_symptomatic):
					host_S.current_compartment = Compartment.objects.get(epidemic=self.epidemic, name='Is')
				else:
					host_S.current_compartment = Compartment.objects.get(epidemic=self.epidemic, name='Ia')
		if host_S.current_compartment != Compartment.objects.get(epidemic=self.epidemic, name='S'):
			host_S.save()
			host_I.save()
			print('infection occurred from host ' + str(host_I.name) + ' to ' + str(host_S.name))
			IE=InfectionEvent.objects.filter(host_infected=host_I).latest('date_infected')
			IE.secondary_infections_succeeded += 1
			IE.save()
			InfectionEvent.objects.create(epidemic=self.epidemic, source_host=host_I, host_infected=host_S, date_infected=timezone.now().replace(tzinfo=utc))
			CompartmentChange.objects.create(epidemic=self.epidemic, host=host_S, source_compartment = Compartment.objects.get(epidemic=self.epidemic, name='S'), destination_compartment=host_S.current_compartment)


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

# misc. libraries
import json
import datetime
import pytz
utc=pytz.UTC
import decimal
import numpy as np

from SetupEpidemic.models import EpidemicSettings, PathogenSettings, InterventionSettings

# Magic to enable json enconding of Decimal object: from https://stackoverflow.com/a/3885198
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


class Epidemic(models.Model):
	name = models.CharField(max_length=140, unique=True, blank=True, default='')
	steps_iterated = models.IntegerField()
	time_last_updated = models.DateTimeField(auto_now_add=True)
	password = models.CharField(max_length=128)
	transmission_rate = models.DecimalField(max_digits = 6, decimal_places=3, default=0)
	
	def __str__(self):
		return self.name

	def create_compartments(self):
		epidemic_settings = EpidemicSettings.objects.get(epidemic=self)
		Compartment.objects.create(name='S',epidemic=self)
		if 'E' in set(list(epidemic_settings.compartmental_model)):
			Compartment.objects.create(name='Es',epidemic=self)
			Compartment.objects.create(name='Ea',epidemic=self)
		if 'I' in set(list(epidemic_settings.compartmental_model)):
			Compartment.objects.create(name='Is',epidemic=self)
			Compartment.objects.create(name='Ia',epidemic=self)
		if 'R' in set(list(epidemic_settings.compartmental_model)):
			Compartment.objects.create(name='R',epidemic=self)
		if epidemic_settings.intervention_available('V'):
			Compartment.objects.create(name='V', epidemic=self)
		if epidemic_settings.intervention_available('M'):
			Compartment.objects.create(name='M', epidemic=self)
		if epidemic_settings.intervention_available('K'):
			Compartment.objects.create(name='K', epidemic=self)
		if epidemic_settings.intervention_available('Q'):
			Compartment.objects.create(name='Q', epidemic=self)
		Compartment.objects.create(name='D',epidemic=self)

	def will_initialize(self):
		epidemic_settings = EpidemicSettings.objects.get(epidemic=self)
		epidemic_settings.N_hosts = len(Host.objects.filter(epidemic=self))
		epidemic_settings.save()
		if epidemic_settings.N_hosts > 0 and self.steps_iterated == 0 and timezone.now().replace(tzinfo=utc) >= epidemic_settings.epidemic_signup_deadline.replace(tzinfo=utc):
			return True
		else:
			return False

	def calculate_transmission_rate(self):
		# Formulas used to calculate transmission rates, back-calculated from R0 assuming continuous time. See TransmissionRateFormulas.nb for details
		epidemic_settings = EpidemicSettings.objects.get(epidemic=self)
		pathogen = PathogenSettings.objects.get(epidemic_settings = epidemic_settings)
		if epidemic_settings.transmission_mode == 'FD':
			return 1-np.exp(-pathogen.R0*(pathogen.virulence + pathogen.recovery_rate))
		else:
			return 1-np.exp(-pathogen.R0*(pathogen.virulence + pathogen.recovery_rate)/decimal.Decimal(epidemic_settings.N_hosts))
		pathogen.save()

	def initialize(self):
		print('run the initialization')
		for compartment in Compartment.objects.filter(epidemic=self):
			if compartment.name in {'Is','Ia','Es','Ea','R','D'}:
				compartment.determine_natural_transition_rates()
			if compartment.name in {'V','M','K','Q'}:
				compartment.determine_intervention_transitions()
		self.transmission_rate = self.calculate_transmission_rate()
		self.save()
		import random
		index_case = random.choice(Host.objects.filter(epidemic=self))
		pathogen_settings = PathogenSettings.objects.get(epidemic_settings = EpidemicSettings.objects.get(epidemic=self))
		# Mark initial infection as an infection event.
		InfectionEvent.objects.create(epidemic=self, host_infected=index_case,  date_infected=timezone.now().replace(tzinfo=utc))
		if np.random.binomial(1,  pathogen_settings.percent_symptomatic):
			index_case.current_compartment = Compartment.objects.get(epidemic=self, name='Is')
		else:
			index_case.current_compartment = Compartment.objects.get(epidemic=self, name='Ia')
		CompartmentChange.objects.create(epidemic=self, host=index_case, source_compartment=Compartment.objects.get(name='S',epidemic=self), destination_compartment=index_case.current_compartment)
		index_case.save()
			  
	def set_password(self, raw_password):
		from django.contrib.auth.hashers import make_password
		self.password = make_password(raw_password)
		self.save()

	def check_password(self, raw_password):
		from django.contrib.auth.hashers import check_password
		return check_password(raw_password, self.password)

	def will_update(self):
		if timezone.now().replace(tzinfo=utc) < EpidemicSettings.objects.get(epidemic=self).epidemic_signup_deadline:
			return False
		if timezone.now().replace(tzinfo=utc) > self.time_last_updated + timezone.timedelta(seconds=float(EpidemicSettings.objects.get(epidemic=self).epidemic_time_step)):
			return True
		else:
			return False
	
	def update_epidemic(self):
		# Simulate transmissions
		from GMF.TransmissionEvent import TransmissionEvent
		transmission_manager = TransmissionEvent(self)
		transmission_manager.simulate_transmission()
		hosts =  Host.objects.filter(epidemic=self).all()
		for host in hosts:
			# since susceptible hosts don't automatically update their state:
			if host.current_compartment.name != 'S':
				host.update_compartment()
		self.steps_iterated += 1
		# Update host compartments
		self.time_last_updated = timezone.now()
		self.save()


class Compartment(models.Model):
	COMPARTMENTS = (
			('S','Susceptible'),
			('Ea','Exposed Asymptomatic'),
			('Es','Exposed Asymptomatic'),
			('Ia','Infectious Asymptomatic'),
			('Is','Infectious Symptomatic'),
			('R','Resistant'),
			('D','Dead'),
			('V', 'Vaccinated'),
			('M', 'Medicated'),
			('K', 'Isolated'), #kakuri
			('Q', 'Quarantined'),
			)
	name = models.CharField(max_length=2, choices=COMPARTMENTS)
	epidemic = models.ForeignKey(Epidemic, on_delete=models.CASCADE)
	transition_rates = models.TextField(blank=True)  # Rather ad hoc, but as JSONField is incompatible with sqlite3, this will take the form of a character value that is Compartment_Key: transition_rate_to_compartment

	def __str__(self):
		return self.name

	def determine_natural_transition_rates(self):
		epidemic_settings = EpidemicSettings.objects.get(epidemic=self.epidemic) #something still feels vaguely antipatterny about this.
		pathogen_settings = PathogenSettings.objects.get(epidemic_settings=epidemic_settings)
		transition_dictionary = {}
		compartment_destinations = {'SI':{'S':['S','Ia','Is'],'Is':['Is','D'],'D': ['D']}, 
					    'SIS':{'S':['S','Ia','Is'],'Is':['Is','S','D'],'Ia':['Ia','S'],'D': ['D']},
					    'SIR':{'S':['S','Ia','Is'],'Is':['Is','R','D'],'Ia':['Ia','R'],'R':['R'],'D':['D']},
					    'SEIR':{'S':['S','Es','Ea'],'Es':['Es','Is'],'Ea':['Ea','Ia'],'Is':['Is','R','D'],'Ia':['Ia','R'],'R':['R'],'D':['D']},
					    'SEIS':{'S':['S','Es','Ea'],'Ea':['Ea','Ia'],'Es':['Es','Is'],'Is':['Is','S','D'],'Ia':['Ia','S'], 'D':['D']},
					    'SEIRS': {'S':['S','Es','Ea'],'Ea':['Ea','Ia'],'Es':['Es','Is'],'Is':['Is','R','D'],'Ia':['Ia','R'],'R':['R','S'],'D': ['D']}
						}
		transition_dictionary_keys = compartment_destinations[epidemic_settings.compartmental_model][self.name]
		# initialize the transition dictionary
		for key in transition_dictionary_keys:
			transition_dictionary[key] = 1
		# Set values from PathogenSettings
		if dict.get(transition_dictionary,'D'):
			transition_dictionary['D'] = pathogen_settings.virulence
		if dict.get(transition_dictionary,'R'):
			transition_dictionary['R'] = pathogen_settings.recovery_rate
		if self.name == 'Ia' and dict.get(transition_dictionary,'S'):
			transition_dictionary['S'] = pathogen_settings.recovery_rate
		if self.name == 'Is' and dict.get(transition_dictionary,'S'):
			transition_dictionary['S'] = pathogen_settings.recovery_rate
		if self.name == 'Ea':
			transition_dictionary['Ia'] = 1-pathogen_settings.incubation_period
		if self.name == 'Es':
			transition_dictionary['Is'] = 1-pathogen_settings.incubation_period
		if self.name == 'R' and dict.get(transition_dictionary,'S'):
			transition_dictionary['S'] = pathogen_settings.immunity_decay
		# The probability of staying in the compartment is just 1-probability of leaving.
		transition_dictionary[self.name] = 1-sum([value for key, value in transition_dictionary.items() if key!=self.name])
		# Renormalize the transition rates: note this will also ensure compartments with only a single member get values=1.
		old_sum = decimal.Decimal(sum(transition_dictionary.values()))
		for key, value in transition_dictionary.items():
			transition_dictionary[key] = value/old_sum
		self.transition_rates = json.dumps(transition_dictionary, cls=DecimalEncoder)
		self.save()

	def determine_intervention_transitions(self):
		# For quarantine and isolation, assume the host enters that compartment as long as they select the intervention
		compartment_destinations = {'V':['S','V'], 'M':['S','Is','R'], 'Q':['Q','Es','K'], 'K':['S','K','Is','Ia','R','D']}
		immunity = 1
		epidemic_settings = EpidemicSettings.objects.get(epidemic=self.epidemic)
		pathogen_settings = PathogenSettings.objects.get(epidemic_settings=epidemic_settings)
		intervention_settings = InterventionSettings.objects.get(epidemic_settings=epidemic_settings)
		if epidemic_settings.compartmental_model in {'SIS','SEIS'}:
			immunity = 0
		transition_dictionaries = {'V':{'S': pathogen_settings.immunity_decay + (1-intervention_settings.vaccine_efficacy), 'V': 1-pathogen_settings.immunity_decay},
					   'M':{'S': (1-immunity) * intervention_settings.drug_efficacy, 'R': immunity * intervention_settings.drug_efficacy, 'Is':1-intervention_settings.drug_efficacy},
					   'Q':{'Q':intervention_settings.quarantine_success, 'Es':1-intervention_settings.quarantine_success, 'K': pathogen_settings.incubation_period,},
					   'K':{'S': (1-immunity) * pathogen_settings.recovery_rate, 'K': intervention_settings.isolation_success,'Is':1-intervention_settings.isolation_success,'R': immunity*pathogen_settings.recovery_rate, 'D':pathogen_settings.virulence}}

		transition_dictionary = transition_dictionaries[self.name]
		old_sum = decimal.Decimal(sum(transition_dictionary.values()))
		for key, value in transition_dictionary.items():
			transition_dictionary[key] = value/old_sum

		self.transition_rates = json.dumps(transition_dictionary, cls=DecimalEncoder)
		self.save()

class Host(models.Model):
	name = models.CharField(max_length=100)
	join_date = models.DateTimeField(auto_now_add=True)
	epidemic = models.ForeignKey(Epidemic, on_delete=models.CASCADE)
	current_compartment = models.ForeignKey(Compartment, on_delete=models.CASCADE)
	transmission_modifier = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=1)
	
	def __str__(self):
		return self.name

	def update_compartment(self):
		old_compartment = self.current_compartment
		transition_dictionary = json.loads(old_compartment.transition_rates)
		new_compartment_name = np.random.choice(list(transition_dictionary.keys()),1, p = list(transition_dictionary.values()))[0]
		if new_compartment_name != old_compartment.name:
			print(str(self.name) + ' has gone from ' + str(old_compartment.name) + ' to ' + str(new_compartment_name) + ' ' + str(transition_dictionary.keys()) + ' ' + str(transition_dictionary.values()))
			self.current_compartment = Compartment.objects.get(epidemic=self.epidemic, name=new_compartment_name)
			CompartmentChange.objects.create(epidemic=self.epidemic, host=self, source_compartment = old_compartment, destination_compartment=self.current_compartment)
			self.save()

class InfectionEvent(models.Model):
	epidemic = models.ForeignKey(Epidemic, on_delete=models.CASCADE)
	source_host = models.ForeignKey(Host, related_name='source_host', on_delete=models.SET_NULL, null=True)
	host_infected = models.ForeignKey(Host, related_name='host_infected', on_delete=models.CASCADE)
	date_infected = models.DateTimeField(auto_now_add=True)
	secondary_infections_attempted = models.IntegerField(default=0)
	secondary_infections_succeeded = models.IntegerField(default=0)

class CompartmentChange(models.Model):
	epidemic = models.ForeignKey(Epidemic, on_delete=models.CASCADE)
	host = models.ForeignKey(Host, on_delete=models.CASCADE)
	source_compartment = models.ForeignKey(Compartment, related_name='source_compartment', on_delete=models.CASCADE)
	destination_compartment = models.ForeignKey(Compartment, related_name='destination_compartment', on_delete=models.CASCADE)
	time_switched = models.DateTimeField(auto_now_add=True)


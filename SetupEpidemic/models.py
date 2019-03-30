# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.crypto import get_random_string
from datetime import datetime
from django.utils import timezone

def one_hour_hence():
	return timezone.now() + timezone.timedelta(hours=1) # https://stackoverflow.com/a/27491426/

def one_month_hence():
	return timezone.now() + timezone.timedelta(months=1) 


class EpidemicSettings(models.Model):
	COMPARTMENTAL_MODELS = (
				('SI','Susceptible-Infectious'),
				('SIS','Susceptible-Infectious-Susceptible'),
				('SIR','Susceptible-Infectious-Resistant'),
				('SEIR','Susceptible-Exposed-Infectious-Resistant'),
				('SEIS','Susceptible-Exposed-Infectious-Susceptible'),
				('SEIRS','Susceptible-Exposed-Infectious-Resistant-Susceptible'),
			)
	TRANSMISSION_MODE = (
				('FD', 'Frequency-dependent'),
				('DD', 'Density-dependent'),
			)

	TIME_STEP = (
				('SEC', 'Seconds'),
				('MIN', 'Minutes'),
				('HR', 'Hours'),
				('DAY', 'Days'),
			)
	epidemic = models.OneToOneField('GMF.Epidemic', on_delete = models.CASCADE, null=True)
	name = models.CharField(max_length=140, unique=True, blank=True, default='')
	random_key = models.CharField(max_length=64, default=get_random_string())
	epidemic_creation_date = models.DateTimeField(auto_now_add=True)
	epidemic_time_step = models.DecimalField(max_digits = 6, decimal_places=3, default=0.017)
	epidemic_signup_deadline = models.DateTimeField(auto_now_add=False, default=one_hour_hence, blank=True)
	transmission_mode = models.CharField(max_length=2, choices=TRANSMISSION_MODE, default='FD')
	hosts_encountered = models.PositiveIntegerField(default=0)
	compartmental_model = models.CharField(max_length = 5, choices=COMPARTMENTAL_MODELS, default='SI')
	N_hosts = models.IntegerField(default=0)
	temp_password = models.CharField(max_length=128,default='')

	def __str__(self):
		return self.name

	def assign_interventions(self, associated_interventions):
		self.intervention_settings = associated_interventions
		self.save()

	def get_deadline(self):
		return self.epidemic_signup_deadline

	def compartment_available(self, compartment):
		import re
		return bool(re.search(compartment, self.compartmental_model))

	def intervention_available(self, intervention):
		answer = False
		intervention_settings = InterventionSettings.objects.get(epidemic_settings=self)
		if intervention=='V':
			if intervention_settings.vaccine_efficacy > 0:
				answer=True
		if intervention=='M':
			if intervention_settings.drug_efficacy > 0:
				answer=True
		if intervention=='K':
			if intervention_settings.isolation_success > 0:
				answer=True
		if intervention=='Q':
			if intervention_settings.quarantine_success > 0:
				answer=True
		if intervention=='B':
			if intervention_settings.transmission_blocking > 0:
				answer=True
		return answer

	def clear_password(self):
		self.temp_password = ''
		self.save()


class PathogenSettings(models.Model):
	PATHOGEN_SPECIES = (
				('PM', 'Poximus maximus'),
				('PP', 'Poximus pandemicus'),
				('PA', 'Poximus acutus'),
				('PI', 'Poximus intermedius'),
				('PF', 'Poximus futilicus'),
				('PN', 'Poximus neoforma'),
			)
	epidemic_settings = models.OneToOneField(EpidemicSettings, on_delete = models.CASCADE, null=True)
	species = models.CharField(max_length=2, choices=PATHOGEN_SPECIES, default='PN')
	transmission_rate = models.DecimalField(max_digits = 5, decimal_places=3, default=0.0)
	virulence = models.DecimalField(max_digits = 5, decimal_places=3)
	R0 = models.DecimalField(max_digits = 5, decimal_places=3, default=1.0)
	percent_symptomatic = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	recovery_rate = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	incubation_period = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	immunity_decay = models.DecimalField(max_digits = 6, validators=[MinValueValidator(0.0), MaxValueValidator(100)], decimal_places=3, default=0)
	random_key = models.CharField(max_length=64, default=get_random_string())
	
	def normalize_values(self):
		import decimal
		if self.incubation_period:
			self.incubation_period /= decimal.Decimal(100.0)
		if self.immunity_decay:
			self.immunity_decay /= decimal.Decimal(100.0)
		self.percent_symptomatic /= decimal.Decimal(100.0)
		if self.species == 'PN':
			self.recovery_rate /= decimal.Decimal(100.0)
			self.virulence /= decimal.Decimal(100.0)
		self.save()


class InterventionSettings(models.Model):
	epidemic_settings = models.OneToOneField(EpidemicSettings, on_delete = models.CASCADE, null=True)
	random_key = models.CharField(max_length=64, default=get_random_string())
	drug_efficacy = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	vaccine_efficacy = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	transmission_blocking = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	isolation_success = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)
	quarantine_success = models.DecimalField(max_digits = 6, decimal_places=3, validators=[MinValueValidator(0.0), MaxValueValidator(100)], default=0)

	def normalize_values(self):
		import decimal
		self.drug_efficacy /= decimal.Decimal(100.0)
		self.vaccine_efficacy /= decimal.Decimal(100.0)
		self.transmission_blocking /= decimal.Decimal(100.0)
		self.isolation_success /= decimal.Decimal(100.0)
		self.quarantine_success /= decimal.Decimal(100.0)


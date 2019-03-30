# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.
from splinter import Browser
import time 


class TestEpidemicSetup(TestCase):
	def setUp(self):
		self.browser=Browser('chrome')
		# browser.visit('http://gmf.hcoop.net')
		self.browser.visit('http://127.0.0.1:8000/')

	def enterSetup(self):
		button = self.browser.find_by_name('configure')
		if len(button):
			button.click()
		else:
			print('Configure button not found')

class TestSetupProcess(TestEpidemicSetup):
	def runAll(self):
		self.setUp()
		self.enterSetup()
		self.runStarts('PI','SIR')
		self.runRemainder('FD',['drug_efficacy','vaccine_efficacy','isolation_success','transmission_blocking'])
		self.runFinalize()

		self.enterSetup()
		self.runStarts('PN','SEIR')
		self.runRemainder('FD',['drug_efficacy','quarantine_success', 'vaccine_efficacy','isolation_success','transmission_blocking'])
		self.runFinalize()

	def runStarts(self, pathogen_abbreviation, compartment_model):
		pathogen_button = self.browser.find_by_name(pathogen_abbreviation)
		if len(pathogen_button):
			pathogen_button.click()
			import time 
			time.sleep(1)
			if pathogen_abbreviation is not 'PN':
				self.browser.find_by_name('confirm_' + pathogen_abbreviation).click()
			else:
				self.browser.find_by_name('confirm_PN').click()
		else:
			print('Pathogen species is incorrectly specified for ' + pathogen_abbreviation + '. Fix before proceeding')
			return
		compartment_button = self.browser.find_by_name(compartment_model)
		if len(compartment_button):
			compartment_button.click()
			time.sleep(2)
			self.browser.find_by_name('confirm_'+compartment_model).click()	
		else:
			print('Compartment model is incorrectly specified for ' + compartment_model + '. Fix before proceeding')
			return

	def runRemainder(self, transmission_mode_abbreviation, interventions):
		transmission_mode_button = self.browser.find_by_name(transmission_mode_abbreviation)
		if len(transmission_mode_button):
			transmission_mode_button.click()
			time.sleep(1)
			self.browser.find_by_name('confirm_'+transmission_mode_abbreviation).click()
		for intervention_quantity in interventions:		
			slider = self.browser.find_by_id(intervention_quantity+'_setter')
			if len(slider):
				self.browser.find_by_id(intervention_quantity + '_setter').mouse_over()
				self.browser.find_by_id(intervention_quantity + '_setter').mouse_out()
		self.browser.find_by_name('submit_interventions').click()
		
	def runFinalize(self, epidemic_name=0):
		time.sleep(1)
		from django.utils.crypto import get_random_string
		if epidemic_name is 0:
			self.browser.fill('epidemic-name',str('test_'+get_random_string(3)))
		else:
			self.browser.fill('epidemic-name', epidemic_name)
		from django.utils import timezone
		import datetime
		import pytz
		utc=pytz.UTC
		self.browser.fill('epidemic-epidemic_signup_deadline',str(timezone.localtime(timezone.now())
 + timezone.timedelta(seconds=45)))
		self.browser.fill('epidemic-temp_password',str(1234))
		self.browser.find_by_name('finalize').click()


from SetupEpidemic.tests import *
#k = TestSetupProcess()
#k.runAll()

class TestPathogens(TestEpidemicSetup):
	def readyMe(self):
		self.setUp()
		self.browser.find_by_name('configure').click()	

	def findPathogen(self, pathogen_abbreviation):
		button = self.browser.find_by_name(pathogen_abbreviation)
		button.click()
		pathogen_link = self.browser.find_link_by_partial_href(pathogen_abbreviation)
		if len(pathogen_link):
			# To do: needs javascript magic
			self.browser.click_link_by_partial_href(pathogen_abbreviation)
		else:
			print('Pathogen modal is incorrectly specified for ' + pathogen_abbreviation + '. Fix before proceeding')
			return
		button = self.browser.find_by_name('start_over')
		button.click()
		self.browser.find_by_name('configure').click()

	def checkPathogens(self):
		self.readyMe()
		findPathogen('PN')
		findPathogen('PM')
		findPathogen('PA')
		findPathogen('PI')
		findPathogen('PP')
		findPathogen('PF')
		print('All pathogens present and successfully accounted for')




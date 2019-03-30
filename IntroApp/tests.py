# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.
class TestDestinations(TestCase):
	def assume_new_user(self):
		# Install chromedriver into /usr/bin (see https://splinter.readthedocs.io/en/latest/drivers/chrome.html), then run:
		from splinter import Browser
		browser=Browser('chrome')
		# browser.visit('http://gmf.hcoop.net')
		browser.visit('http://127.0.0.1:8000/')
		button = browser.find_by_name('configure')
		button.click()
		try:
			self.assertTrue(browser.is_text_present('Choose a pathogen'))
		except:
			print('Configure an epidemic button isn\'t working as expected. Fix before proceeding')
			return
		button = browser.find_by_name('start_over')
		button.click()
		button = browser.find_by_name('check_status')
		button.click()
		try:
			self.assertTrue(browser.is_text_present('Login to an epidemic'))
		except:
			print('Behavior of new user logging in to an epidemic for the first time is wrong. Fix before proceeding')
			return
		button = browser.find_by_name('start_over')
		button.click()
		button = browser.find_by_name('join')
		button.click()
		try:
			self.assertTrue(browser.is_text_present('Login to an epidemic'))
		except:
			print('Behavior of joining an epidemic is wrong. Fix before proceeding')
			return
		button = browser.find_by_name('start_over')
		button.click()
		button=browser.find_by_name('download')
		try:
			self.assertTrue(browser.is_text_present('Download an epidemic'))
		except:
			print('Process of downloading an epidemic is wrong. Fix before proceeding')
			return
		browser.quit()
		print('All unit tests passed for a new user')

	def assume_returning_user(self):
		# Install chromedriver into /usr/bin, then run:
		from splinter import Browser
		browser=Browser('chrome')
		# browser.visit('http://gmf.hcoop.net')
		browser.visit('http://127.0.0.1:8000/')
		button = browser.find_by_name('configure')
		button.click()
		try:
			self.assertTrue(browser.is_text_present('Choose a pathogen'))
		except:
			print('Configure an epidemic button isn\'t working as expected. Fix before proceeding')
			return
		button = browser.find_by_name('start_over')
		button.click()
		button = browser.find_by_name('check_status')
		button.click()
		try:
			self.assertFalse(browser.is_text_present('Login to an epidemic'))
			print('Expect returning user to not have to relogin to an epidemic to check status. Fix before proceeding')
			return
		except:
			print('Check stuff under CheckStatus')
		button = browser.find_by_name('start_over')
		button.click()
		button = browser.find_by_name('join')
		button.click()
		try:
			self.assertTrue(browser.is_text_present('Login to an epidemic'))
		except:
			print('Behavior of joining an epidemic is wrong. Fix before proceeding')
			return
		button = browser.find_by_name('start_over')
		button.click()
		button=browser.find_by_name('download')
		try:
			self.assertTrue(browser.is_text_present('Download an epidemic'))
		except:
			print('Process of downloading an epidemic is wrong. Fix before proceeding')
			return
		browser.quit()
		print('All unit tests passed for a new user')

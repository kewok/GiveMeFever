from django.test import TestCase
from django.utils.crypto import get_random_string

# Create your tests here.
from splinter import Browser
import time 


class TestJoiningEpidemic(TestCase):
	def setUp(self):
		self.browser=Browser('chrome')
		# browser.visit('http://gmf.hcoop.net')
		self.browser.visit('http://127.0.0.1:8000/')

	def enterJoin(self):
		button = self.browser.find_by_name('join')
		if len(button):
			button.click()
		else:
			print('Join button not found')

	def signUp(self, user_name, epidemic_name):
		self.browser.fill('name',user_name)
		self.browser.fill('associated_epidemic_name', epidemic_name)
		time.sleep(1)
		self.browser.find_by_name('join').click()
		if self.browser.find_link_by_partial_href('ShowHistory'):
			self.browser.click_link_by_partial_href('CheckStatus/StartOver')
		else:
			self.browser.find_by_name('start_over').click()
		


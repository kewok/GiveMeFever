from django.test import TestCase

# Create your tests here.
from splinter import Browser
import sys
sys.path.append('..')

class TestCheckStatus(TestCase):
	def setUp(self):
		self.browser=Browser('chrome')
		# browser.visit('http://gmf.hcoop.net')
		self.browser.visit('http://127.0.0.1:8000/')

	def CheckStatus(self):
		self.browser.find_by_name('check_status').click()	

class TestNewHost(TestCheckStatus):
	def clickWrong(self):
		self.CheckStatus
		

class ReturningHost(TestCheckStatus):
	def checkBack(self):
		self.CheckStatus()
	
	

	

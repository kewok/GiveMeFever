from __future__ import unicode_literals

from django.db import models
from django.utils.crypto import get_random_string
from GMF.models import Host

class HostSettings(models.Model):
	host = models.OneToOneField(Host, on_delete=models.CASCADE, null=True)
	name = models.CharField(max_length=140, blank=True, default='')
	epidemic_join_date = models.DateTimeField(auto_now_add=True)	
	associated_epidemic_name = models.CharField(max_length=140, blank=True, default=None)
	random_key = models.CharField(max_length=64, default=get_random_string())

	def __str__(self):
		return(self.name)


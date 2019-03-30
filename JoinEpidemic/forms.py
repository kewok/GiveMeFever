from django import forms 
from django.forms.models import modelformset_factory
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import HostSettings
from SetupEpidemic.models import EpidemicSettings
from GMF.models import Host

class HostForm(forms.ModelForm):
	class Meta:
		model = HostSettings
		fields = ('name', 'associated_epidemic_name', )
		labels = {'name': 'Your name', 'associated_epidemic_name': 'Disease name'}

	# return error if epidemic doesn't exist: https://stackoverflow.com/a/3090342
	def clean_associated_epidemic_name(self):
		associated_epidemic_name = self.cleaned_data['associated_epidemic_name']
		if associated_epidemic_name is None:
			raise ValidationError("Epidemic name must be provided!")
		try:
			outcome = EpidemicSettings.objects.get(name=associated_epidemic_name)
		except EpidemicSettings.DoesNotExist:
			outcome = None
			raise ValidationError("Epidemic does not yet exist!")
		from datetime import datetime
		print('deadline time is ' + str(outcome.epidemic_signup_deadline))
		if outcome.epidemic_signup_deadline < timezone.now():
			host_name = self.cleaned_data['name']
			if not Host.objects.filter(epidemic__name=associated_epidemic_name, name=host_name).exists():
				outcome = None
				raise ValidationError("Signup period for this epidemic has ended :(")
		return associated_epidemic_name

	def clean_name(self):
		host_name = self.cleaned_data['name']
		if host_name is None:
			raise ValidationError('Host must have a name')
		associated_epidemic_name = self.data.get('associated_epidemic_name')
		return host_name

	def get_epidemic_name(self):
		return self.instance.associated_epidemic_name

	def __str__(self):
		return str(self.instance)


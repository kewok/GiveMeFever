from django import forms 
from django.forms.models import modelformset_factory
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.utils import timezone

from GMF.models import Epidemic

class EpidemicForm(forms.Form):
	disease_name = forms.CharField(max_length=140)
	epidemic_password = forms.CharField(max_length=128,required=False)

	def clean(self):
		cleaned_data = super(EpidemicForm, self).clean()
		requested_disease_name = cleaned_data.get('disease_name')
		requested_epidemic_password = cleaned_data.get('epidemic_password')
		try: 
			outcome = Epidemic.objects.get(name=requested_disease_name)
			requested_epidemic_password = self.cleaned_data['epidemic_password']
			validate = outcome.check_password(str(requested_epidemic_password))
			if not validate:
				outcome = None
				raise ValidationError("Password is incorrect!")
		except Epidemic.DoesNotExist:
			outcome = None
			raise ValidationError("Epidemic does not yet exist!")

	def get_disease_name(self):
		return self.cleaned_data['disease_name']

	def __str__(self):
		return str(self.instance)


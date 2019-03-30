from django import forms 
from django.forms.models import modelformset_factory
from django.utils.crypto import get_random_string
from .models import PathogenSettings, EpidemicSettings, InterventionSettings
from django.core.exceptions import ValidationError
from betterforms.multiform import MultiModelForm


class PathogenForm(forms.ModelForm):
	immunity_decay = forms.DecimalField(widget=forms.HiddenInput(), required=False, initial=0.0)
	incubation_period = forms.DecimalField(widget=forms.HiddenInput(), required=False, initial=0.0)
	# The following 3 fields are only required for the customized pathogen 
	recovery_rate = forms.DecimalField(widget=forms.HiddenInput(), required=False, initial=0.0)
	virulence = forms.DecimalField(widget=forms.HiddenInput(), required=False, initial=0.0)
	R0 = forms.DecimalField(widget=forms.HiddenInput(), required=False, initial=0.0)

	class Meta:
		model = PathogenSettings
		fields = ('species', 'incubation_period', 'immunity_decay', 'percent_symptomatic','recovery_rate', 'virulence', 'R0' )
		widgets = {'species': forms.HiddenInput(), 'percent_symptomatic':forms.HiddenInput(), }

	def set_key(self, key_value):
		self.instance.random_key = key_value

	def finalize_values(self):
		if self.cleaned_data['species'] != 'PN':
			high_virulence = 0.1 # an average of 9 time steps before host death
			low_virulence = 0.02 # an average of 49 time steps before host death

			high_recovery_rate = 0.15 
			low_recovery_rate = 0.015

			pathogen_dictionaries = {
				'PM': {'R0': 10.0, 'virulence': high_virulence, 'recovery_rate': high_recovery_rate},
				'PP': {'R0': 10.0, 'virulence': low_virulence, 'recovery_rate': high_recovery_rate},
				'PA': {'R0': 1.01, 'virulence': high_virulence, 'recovery_rate': low_recovery_rate},
				'PI': {'R0': 1.0, 'virulence': round((high_virulence + low_virulence)/2.0,3), 'recovery_rate': round((high_recovery_rate + low_recovery_rate)/2.0,3)},
				'PF': {'R0': 0.99, 'virulence': low_virulence, 'recovery_rate': high_recovery_rate},
				}
			self.instance.R0 = pathogen_dictionaries[self.cleaned_data['species']]['R0']
			self.instance.virulence = pathogen_dictionaries[self.cleaned_data['species']]['virulence']
			self.instance.recovery_rate = pathogen_dictionaries[self.cleaned_data['species']]['recovery_rate']
		if not self.cleaned_data['immunity_decay']:
			self.instance.immunity_decay = 0
		if not self.cleaned_data['incubation_period']:
			self.instance.incubation_period = 0

class InterventionForm(forms.ModelForm):
	quarantine_success = forms.DecimalField(widget=forms.HiddenInput(), required=False)
	vaccine_efficacy = forms.DecimalField(widget=forms.HiddenInput(), required=False)
	class Meta:
		model = InterventionSettings
		fields = ('drug_efficacy', 'vaccine_efficacy','quarantine_success', 'transmission_blocking','isolation_success', )
		widgets = {'drug_efficacy': forms.HiddenInput(), 'transmission_blocking': forms.HiddenInput(), 'isolation_success': forms.HiddenInput(),  }

	def set_key(self, key_value):
		self.instance.random_key = key_value


class EpidemicForm(forms.ModelForm):
	temp_password = forms.CharField(required=False, label='Optional password to download epidemic data (warning: there is no password recovery!)')
	hosts_encountered = forms.DecimalField(widget=forms.HiddenInput(), required=False)

	class Meta:
		model = EpidemicSettings
		fields = ('epidemic_signup_deadline','name','temp_password', 'epidemic_time_step','transmission_mode','hosts_encountered','compartmental_model', )
		labels = {
			'epidemic_signup_deadline': 'Date by which hosts must join the epidemic (your local time); default 1 hour from now.',
			'name': 'Disease name',
			'epidemic_time_step': 'Minimum epidemic timestep (in minutes; fractions allowed)',
			}
		widgets = {'transmission_mode': forms.HiddenInput(), 'compartmental_model': forms.HiddenInput(),}

	def clean_epidemic_signup_deadline(self):
		signup_deadline = self.cleaned_data['epidemic_signup_deadline']
		from django.utils import timezone
		import datetime
		import pytz
		utc=pytz.UTC
		if signup_deadline.replace(tzinfo=utc) < timezone.datetime.today().replace(tzinfo=utc):
			signup_deadline = None
			raise ValidationError('Sign-up deadline cannot have already passed')
		return signup_deadline

	def clean_name(self):
		epidemic_name = self.cleaned_data['name']
		if epidemic_name is None:
			print('Nonsense')
			epidemic_name = None
			raise ValidationError('Your epidemic needs to be called something')
		if EpidemicSettings.objects.filter(name=epidemic_name).exists():
			print('epidemic already exists')
			epidemic_name = None
			raise ValidationError('Epidemic name must be unique')
		return epidemic_name

	def set_key(self, key_value):
		self.instance.random_key = key_value


# Bring these all together

class EpidemicInitializationForm(MultiModelForm):
	form_classes = {'pathogen': PathogenForm,
			'interventions': InterventionForm,
			'epidemic': EpidemicForm,}

	def finalize(self):
		self.set_random_key()
		self['pathogen'].finalize_values()
		from GMF.models import Epidemic
		new_epidemic = Epidemic.objects.create(steps_iterated=0, name=str(self['epidemic'].cleaned_data['name']))
		# Assign the epidemic settings to this epidemic
		self['epidemic'].instance.epidemic = new_epidemic
		self['epidemic'].instance.save()
		self['interventions'].instance.epidemic_settings = self['epidemic'].instance
		self['interventions'].instance.save()
		self['pathogen'].instance.epidemic_settings = self['epidemic'].instance
		self['pathogen'].instance.save()
		self['interventions'].instance.normalize_values()
		self['pathogen'].instance.normalize_values()
		new_epidemic.create_compartments()
		new_epidemic.set_password(self['epidemic'].cleaned_data['temp_password'])

	def set_random_key(self):
		random_key = get_random_string(64)
		self['pathogen'].set_key(random_key)
		self['interventions'].set_key(random_key)
		self['epidemic'].set_key(random_key)
		


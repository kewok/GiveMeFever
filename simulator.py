# This is the python code to update the epidemic as needed in the background
# To run the script: python manage.py shell < this_script.py
import datetime
import dateutil
from dateutil import relativedelta
import schedule
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GMF.settings")
import django
django.setup()
from GMF.models import Epidemic
from SetupEpidemic.models import EpidemicSettings, PathogenSettings, InterventionSettings

def delete_epidemics():
	epidemics = Epidemic.objects.all()
	from django.utils import timezone
	for epidemic in epidemics:
		if timezone.now() >= EpidemicSettings.objects.get(epidemic=epidemic).epidemic_signup_deadline + relativedelta.relativedelta(months=1):
			epidemic.delete()


# courtesy of https://stackoverflow.com/a/30393162
schedule.every().day.at("01:00").do(delete_epidemics)

import os
f=open('/afs/hcoop.net/user/k/kw/kwo/givemefever_development/pid_simulator.txt','w')
f.write(str(os.getpid()))
f.close()

while True:
        allEpidemics = Epidemic.objects.all()
        for epidemic in allEpidemics:
            if epidemic.will_initialize():
                epidemic.initialize()
                epidemic.save()
            if epidemic.will_update():
                epidemic.update_epidemic()
                epidemic.save()
        schedule.run_pending()

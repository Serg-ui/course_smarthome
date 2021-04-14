from __future__ import absolute_import, unicode_literals
from celery import task
from django.conf import settings
from .models import Setting
import requests
import json


@task()
def smart_home_manager():
    # Здесь ваш код для проверки условий
    # docker exec -it final_web_1 celery -A coursera_house worker -B -l info
    # docker exec -it final_web_1 flower -A coursera_house --port=5555 --broker=redis://redis:6379

    #r = requests.get(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
    #r = r.json()
    #res = next((sub for sub in r['data'] if sub['name'] == 'bedroom_temperature'), None)
    #return res['value']

    s = Setting.objects.all()
    print(s[2].label)
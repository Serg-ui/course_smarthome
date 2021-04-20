from __future__ import absolute_import, unicode_literals
from celery import task
from django.conf import settings
from .models import Setting
import requests
import json
from .Controls import *
import redis
from distutils.util import strtobool


red = redis.Redis(host='redis')
not_controls = ['bedroom_temperature', 'outdoor_light', 'boiler_temperature']
Notifier.subscribe(Events.smoke_detector.name, [ColdWater, HotWater, WashingMachine, Boiler])

r = requests.get(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
r = r.json()

sensors = {}
controls = {}
for i in r['data']:
    if i['name'] in not_controls:
        sensors[i['name']] = str(i['value'])
    else:
        controls[i['name']] = str(i['value'])

red.set('data_controls', json.dumps(controls))
red.set('data_sensors', json.dumps(sensors))

@task()
def smart_home_manager():
    # Здесь ваш код для проверки условий
    # docker exec -it final_web_1 celery -A coursera_house worker -B -l info
    # docker exec -it final_web_1 flower -A coursera_house --port=5555 --broker=redis://redis:6379

    r = requests.get(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
    r = r.json()

    sensors = {}
    controls = {}
    for i in r['data']:
        if i['name'] in not_controls:
            sensors[i['name']] = str(i['value'])
        else:
            controls[i['name']] = str(i['value'])

    controls_from_redis = json.loads(red.get('data_controls'))

    diff_controls = {k: controls[k] for k in controls if
                     k in controls_from_redis and controls[k] != controls_from_redis[k]}

    if diff_controls:
        red.set('data_controls', json.dumps(controls))
        for k, v in diff_controls.items():
            print(f'{k} - {strtobool(v)}')
            Notifier.dispatch(k, bool(strtobool(v)))
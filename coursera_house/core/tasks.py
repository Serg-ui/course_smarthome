from __future__ import absolute_import, unicode_literals
from celery import task
from django.conf import settings
from .models import Setting
import requests
import json
from .Controls import *
import redis
from distutils.util import strtobool


red = redis.Redis(host='redis', decode_responses=True)
not_controls = ['bedroom_temperature', 'outdoor_light', 'boiler_temperature']
Notifier.subscribe(Events.bedroom_presence.name, [ColdWater, HotWater, Boiler, WashingMachine])
Notifier.subscribe(Events.cold_water.name, [Boiler, WashingMachine])
Notifier.subscribe(Events.boiler.name, [Boiler])

r = requests.get(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
r = r.json()

sensors = {}
controls = {}
for i in r['data']:
    if i['name'] in not_controls:
        sensors[i['name']] = str(i['value'])
    else:
        controls[i['name']] = str(i['value'])

red.hmset('data_controls', controls)



@task()
def smart_home_manager():
    # Здесь ваш код для проверки условий
    # docker exec -it final_web_1 celery -A coursera_house worker -B -l info
    # docker exec -it final_web_1 flower -A coursera_house --port=5555 --broker=redis://redis:6379

    r = requests.get(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
    r = r.json()

    if red.exists(Controls.key_to_server):
        red.delete(Controls.key_to_server)

    sensors = {}
    controls = {}
    for i in r['data']:
        if i['name'] in not_controls:
            sensors[i['name']] = str(i['value'])
        else:
            controls[i['name']] = str(i['value'])

    controls_from_redis = red.hgetall('data_controls')

    diff_controls = {k: controls[k] for k in controls if
                     k in controls_from_redis and controls[k] != controls_from_redis[k]}

    if diff_controls:
        for k, v in diff_controls.items():
            red.hset('data_controls', k, v)
            print(f'{k} - {strtobool(v)}')
            Notifier.dispatch(k, bool(strtobool(v)))

    print(red.hgetall(Controls.key_to_server))
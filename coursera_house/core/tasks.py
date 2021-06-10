from __future__ import absolute_import, unicode_literals
from celery import task
from django.conf import settings
from .models import Setting
import requests
import json
from .Controls import *
import redis
from distutils.util import strtobool
import operator
import random

events = ['leak_detector', 'cold_water', 'smoke_detector', 'washing_machine']
not_controls = ['bedroom_temperature', 'outdoor_light', 'boiler_temperature']

Notifier.subscribe(Events.leak_detector.name, [ColdWater, HotWater, Boiler, WashingMachine])
Notifier.subscribe(Events.cold_water.name, [Boiler, WashingMachine])
Notifier.subscribe(Events.boiler.name, [Boiler])
Notifier.subscribe(Events.smoke_detector.name, [AirConditioner, Boiler, WashingMachine, BedroomLight, BathroomLight])


def get_data():
    try:
        data = requests.get(settings.SMART_HOME_API_URL,
                            headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
    except requests.exceptions.RequestException:
        return 'error'

    if data.status_code != 200:
        return 'error'

    try:
        data_json = data.json()
    except json.JSONDecodeError:
        return 'error'

    return sort_data(data_json)


def sort_data(data):
    alarms = {}
    sensors = {}
    controls = {}

    for i in data['data']:
        if i['name'] in not_controls:
            sensors[i['name']] = str(i['value'])
        elif i['name'] in events:
            alarms[i['name']] = str(i['value'])
        else:
            controls[i['name']] = str(i['value'])

    return {'sensors': sensors, 'controls': controls, 'alarms': alarms}


@task()
def smart_home_manager():
    # docker exec -it final_web_1 celery -A coursera_house worker -B -l info

    # docker exec -it final_web_1 celery -A coursera_house.celery:app worker --pool=solo -l info
    # docker exec -it final_web_1 celery -A coursera_house.celery:app beat -l info

    Data.clear()
    d = get_data()
    if d == 'error':
        return

    Data.data = d

    diff_alarms = Data.compare()
    if diff_alarms:
        for k, v in diff_alarms.items():
            print(f'{k} - {v}')
            try:
                Notifier.dispatch(k, bool(strtobool(v)))
            except ValueError:
                Notifier.dispatch(k, v)

    keep('hot_water_target_temperature', 'boiler_temperature', Boiler,
         ops={'<': operator.lt, '>': operator.gt})
    keep('bedroom_target_temperature', 'bedroom_temperature', AirConditioner,
         ops={'>': operator.lt, '<': operator.gt})

    lights()
    if Data.data_to_server:
        print(Data.data_to_server)
        send_post(Data.data_to_server)


def send_post(data):
    data2 = {
        "controllers": []
    }

    for k, v in data.items():
        not_bool = ['on', 'off']
        if v not in not_bool:
            try:
                v = bool(strtobool(v))
            except ValueError:
                pass

        data2['controllers'].append({'name': k, 'value': v})

    try:
        r = requests.post(settings.SMART_HOME_API_URL,
                          headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'},
                          data=json.dumps(data2))
        data = sort_data(r.json())

        Data.data = data
        Data.default_alarms = data['alarms']

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def keep(target, current, obj, ops):
    try:
        target2 = int(Setting.objects.get(controller_name=target).value)
        current2 = int(Data.data['sensors'][current])

        if ops['<'](current2, target2 * 0.9) and not strtobool(Data.data['controls'][obj.name]):
            obj.update(obj.name, True)

        elif ops['>'](current2, target2 * 1.1) and strtobool(Data.data['controls'][obj.name]):
            obj.update(obj.name, False)

    except ValueError:
        pass


def lights():
    outdoor_light = int(Data.data['sensors']['outdoor_light'])
    current_from_server = Data.data['controls']['curtains']

    if outdoor_light < 50:
        Curtains.on(current_from_server)
    else:
        Curtains.off(current_from_server)

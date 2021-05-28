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

default_alarms = {
    'smoke_detector': 'False',
    'cold_water': 'False',
    'washing_machine': 'off',
    'leak_detector': 'False'}

red = redis.Redis(host='redis', decode_responses=True)

events = ['leak_detector', 'cold_water', 'smoke_detector', 'washing_machine']
not_controls = ['bedroom_temperature', 'outdoor_light', 'boiler_temperature']

Notifier.subscribe(Events.leak_detector.name, [ColdWater, HotWater, Boiler, WashingMachine])
Notifier.subscribe(Events.cold_water.name, [Boiler, WashingMachine])
Notifier.subscribe(Events.boiler.name, [Boiler])
Notifier.subscribe(Events.smoke_detector.name, [AirConditioner, Boiler, WashingMachine, BedroomLight])


def get_data():
    try:
        r = requests.get(settings.SMART_HOME_API_URL,
                         headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
        r = r.json()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return sort_data(r)


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


tmp_data = get_data()
red.hmset('data_controls', tmp_data['controls'])
red.hmset('data_alarms', default_alarms)
del tmp_data


@task()
def smart_home_manager():
    # Здесь ваш код для проверки условий
    # docker exec -it final_web_1 celery -A coursera_house worker -B -l info
    # docker exec -it final_web_1 flower -A coursera_house --port=5555 --broker=redis://redis:6379

    global data_from_server
    data_from_server = get_data()

    if red.exists(Controls.key_to_server):
        red.delete(Controls.key_to_server)

    alarms_from_redis = red.hgetall('data_alarms')

    diff_alarms = {k: data_from_server['alarms'][k] for k in data_from_server['alarms'] if
                     k in alarms_from_redis and data_from_server['alarms'][k] != alarms_from_redis[k]}

    if diff_alarms:
        for k, v in diff_alarms.items():
            red.hset('data_alarms', k, v)
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

    data_to_server = red.hgetall(Controls.key_to_server)
    if data_to_server:
        print(data_to_server)
        send_post(data_to_server)


def send_post(data):
    data2 = {
        "controllers": []
    }

    for k, v in data.items():
        data2['controllers'].append({'name': k, 'value': v})

    try:
        r = requests.post(settings.SMART_HOME_API_URL, headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'}, data=json.dumps(data2))
        data = sort_data(r.json())
        red.hmset('data_controls', data['controls'])
        red.hmset('data_alarms', data['alarms'])
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def keep(target, current, obj, ops):

    try:
        target2 = int(Setting.objects.get(controller_name=target).value)
        current2 = int(data_from_server['sensors'][current])

        if ops['<'](current2, target2 * 0.9) and not strtobool(data_from_server['controls'][obj.name]):
            obj.update(obj.name, True)

        elif ops['>'](current2, target2 * 1.1) and strtobool(data_from_server['controls'][obj.name]):
            obj.update(obj.name, False)

    except ValueError:
        pass


def lights():
    outdoor_light = int(data_from_server['sensors']['outdoor_light'])
    current_from_server = data_from_server['controls']['curtains']
    bedroom_light = strtobool(data_from_server['controls']['bedroom_light'])
    bedroom_light_db = Setting.objects.get(controller_name='bedroom_light')



    if bedroom_light_db.value != bedroom_light:
        BedroomLight.update(BedroomLight.name, bedroom_light_db.value)

    if outdoor_light < 50:
        Curtains.on(current_from_server)
    else:
        Curtains.off(current_from_server)

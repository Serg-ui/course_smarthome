from abc import ABC, abstractmethod
from .Events import *
from django.core.mail import send_mail

from .models import Setting


class Data:
    data = {}
    default_alarms = {
        'smoke_detector': 'False',
        'cold_water': 'False',
        'washing_machine': 'off',
        'leak_detector': 'False'}
    data_to_server = {}

    @classmethod
    def hget(cls, key1, key2):
        return cls.data[key1].get(key2)

    @classmethod
    def hset(cls, key, val):
        cls.data_to_server[key] = val

    @classmethod
    def clear(cls):
        cls.data_to_server = {}

    @classmethod
    def compare(cls):
        diff = {k: cls.data['alarms'][k] for k in cls.data['alarms'] if
                    k in cls.default_alarms and cls.data['alarms'][k] != cls.default_alarms[k]}
        if diff:
            cls.default_alarms = cls.data['alarms']

        return diff






class Controls(ABC):
    name = ''
    key_alarms = 'data_alarms'
    key_to_server = 'data_to_server'
    key_controls = 'data_controls'

    ON = 'True'
    OFF = 'False'
    BLOCK = ''

    @abstractmethod
    def update(self, event, value):
        pass

    @classmethod
    def switch_on(cls):
        Data.hset(cls.name, cls.ON)
        print(f'{cls.name} - Включен')

    @classmethod
    def leak(cls, value):
        if value:
            Data.hset(cls.name, cls.OFF)
            print(f'Протечка, {cls.name} - False')
        else:
            print(f'Протечка устранена, {cls.name}')


class ColdWater(Controls):
    name = Events.cold_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if not value:
                cls.switch_on()
            cls.leak(value)

        if event == cls.name:
            pass


class HotWater(Controls):
    name = Events.hot_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if not value:
                cls.switch_on()
            cls.leak(value)

        if event == cls.name:
            pass


class Boiler(Controls):
    name = Events.boiler.name
    DEPENDS = {Events.cold_water.name: 'True'}

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if not value:
                pass

            cls.leak(value)

        if event == Events.cold_water.name:
            if not value:
                Data.hset(cls.name, cls.OFF)
                print('Бойлер выключен из-за перекрытия холодной воды')

        if event == cls.name:
            if value:
                water = Data.hget(cls.key_alarms, Events.cold_water.name)
                smoke = Data.hget(cls.key_alarms, Events.smoke_detector.name)
                leak = Data.hget(cls.key_alarms, Events.leak_detector.name)

                if water == 'True' and smoke == 'False' and leak == 'False':
                    Data.hset(cls.name, cls.ON)
                    print('Бойлер вкл')
            else:
                Data.hset(cls.name, cls.OFF)
                print('Бойлер выкл')

        if event == Events.smoke_detector.name:
            if value:
                Data.hset(cls.name, cls.OFF)


class WashingMachine(Controls):
    name = Events.washing_machine.name
    ON = 'on'
    OFF = 'off'
    BLOCK = 'broken'
    DEPENDS = {Events.cold_water.name: 'True'}

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if not value:
                if Data.hget(cls.key_alarms, Events.smoke_detector.name) == 'False':
                    #cls.switch_on()
                    pass
                else:
                    print('Невозможно вкл cт. машину из-за задымления')
            else:
                if Data.hget(cls.key_alarms, cls.name) != cls.BLOCK:
                    cls.leak(value)

        if event == Events.cold_water.name:
            if not value:
                Data.hset(cls.name, cls.OFF)
                print('Стиральная машина выключена из-за перекрытия холодной воды')

        if event == Events.smoke_detector.name:
            if value:
                if Data.hget(cls.key_alarms, cls.name) != cls.BLOCK:
                    Data.hset(cls.name, cls.OFF)


class AirConditioner(Controls):
    name = Events.air_conditioner.name

    @classmethod
    def update(cls, event, value):
        if event == cls.name:
            if value:
                smoke = Data.hget(cls.key_alarms, Events.smoke_detector.name)
                if smoke == 'False':
                    Data.hset(cls.name, cls.ON)
            else:
                Data.hset(cls.name, cls.OFF)

        if event == Events.smoke_detector.name:
            if value:
                Data.hset(cls.name, cls.OFF)


class LightBase(Controls):
    @classmethod
    def update(cls, event, value):
        if event == cls.name:
            if value:
                if Data.hget(cls.key_alarms, Events.smoke_detector.name) == 'False':
                    Data.hset(cls.name, cls.ON)
                    current_db = Setting.objects.get(controller_name=cls.name)
                    current_db.value = 1
                    current_db.save()
            else:
                Data.hset(cls.name, cls.OFF)
                current_db = Setting.objects.get(controller_name=cls.name)
                current_db.value = 0
                current_db.save()

        if event == Events.smoke_detector.name:
            if value:
                if Data.hget(cls.key_controls, cls.name) != cls.OFF:
                    Data.hset(cls.name, cls.OFF)
                    current_db = Setting.objects.get(controller_name=cls.name)
                    current_db.value = 0
                    current_db.save()


class BedroomLight(LightBase):
    name = Events.bedroom_light.name


class BathroomLight(LightBase):
    name = Events.bathroom_light.name


class Curtains(Controls):
    name = Events.curtains.name
    ON = 'open'
    OFF = 'close'
    BLOCK = 'slightly_open'

    @classmethod
    def update(cls, event):
        pass

    @classmethod
    def on(cls, value):
        if value != cls.BLOCK and value != cls.ON and Data.hget(cls.key_controls, BedroomLight.name) == BedroomLight.OFF:
            Data.hset(cls.name, cls.ON)

    @classmethod
    def off(cls, value):
        if value != cls.BLOCK and value != cls.OFF and Data.hget(cls.key_controls, BedroomLight.name) == BedroomLight.ON:
            Data.hset(cls.name, cls.OFF)



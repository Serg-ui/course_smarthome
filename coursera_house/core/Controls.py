from abc import ABC, abstractmethod
from .Events import *
from django.core.mail import send_mail
from django.conf import settings


class Data:
    data = {}
    default_alarms = {
        'smoke_detector': 'False',
        'cold_water': 'True',
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
    def compare_alarms(cls):
        diff = {k: cls.data['alarms'][k] for k in cls.data['alarms'] if
                k in cls.default_alarms and cls.data['alarms'][k] != cls.default_alarms[k]}
        if diff:
            cls.default_alarms = cls.data['alarms']

        return diff


class Controls(ABC):
    name = ''
    key_alarms = 'alarms'
    key_to_server = 'data_to_server'
    key_controls = 'controls'

    ON = 'True'
    OFF = 'False'
    BLOCK = ''

    value = ''

    @abstractmethod
    def update(self, event, value):
        pass

    @classmethod
    def switch(cls, value):
        current = Data.hget(cls.key_controls, cls.name)
        if value != current and current != cls.BLOCK and value != cls.BLOCK:
            Data.hset(cls.name, value)


class ColdWater(Controls):
    name = Events.cold_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if value:
                cls.switch(cls.OFF)

                send_mail(
                    'leak detector',
                    'leak detector = true',
                    'from@smarthome.com',
                    [settings.EMAIL_RECEPIENT],
                    fail_silently=False,
                )


class HotWater(Controls):
    name = Events.hot_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if value:
                cls.switch(cls.OFF)


class Boiler(Controls):
    name = Events.boiler.name

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if value:
                cls.switch(cls.OFF)

        if event == Events.cold_water.name:
            if not value:
                cls.switch(cls.OFF)

        if event == cls.name:
            if value:
                water = Data.hget(cls.key_alarms, Events.cold_water.name)
                smoke = Data.hget(cls.key_alarms, Events.smoke_detector.name)
                leak = Data.hget(cls.key_alarms, Events.leak_detector.name)

                if water == 'True' and smoke == 'False' and leak == 'False':
                    cls.switch(cls.ON)

            else:
                cls.switch(cls.OFF)

        if event == Events.smoke_detector.name:
            if value:
                cls.switch(cls.OFF)


class WashingMachine(Controls):
    name = Events.washing_machine.name
    ON = 'on'
    OFF = 'off'
    BLOCK = 'broken'

    @classmethod
    def update(cls, event, value):
        if event == Events.leak_detector.name:
            if value:
                if Data.hget(cls.key_controls, cls.name) != cls.OFF:
                    Data.hset(cls.name, cls.OFF)

        if event == Events.cold_water.name:
            if not value:
                cls.switch(cls.OFF)

        if event == Events.smoke_detector.name:
            if value:
                cls.switch(cls.OFF)


class AirConditioner(Controls):
    name = Events.air_conditioner.name

    @classmethod
    def update(cls, event, value):
        if event == cls.name:
            if value:
                smoke = Data.hget(cls.key_alarms, Events.smoke_detector.name)
                if smoke == 'False':
                    cls.switch(cls.ON)
            else:
                cls.switch(cls.OFF)

        if event == Events.smoke_detector.name:
            if value:
                cls.switch(cls.OFF)


class LightBase(Controls):
    @classmethod
    def update(cls, event, value):

        if event == Events.smoke_detector.name:
            if value:
                cls.switch(cls.OFF)


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

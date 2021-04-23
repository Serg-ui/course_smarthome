from abc import ABC, abstractmethod
from .Events import *
from django.core.mail import send_mail
import redis


red = redis.Redis(host='redis', decode_responses=True)


class Controls(ABC):
    key_controls = 'data_controls'
    key_to_server = 'data_to_server'

    ON = 'True'
    OFF = 'False'
    BLOCK = ''

    @abstractmethod
    def update(self, event, value):
        pass

    @classmethod
    def switch(cls, value, depends_event='False'):
        if value:
            if red.hget(cls.key_controls, depends_event) == 'True':
                print(f'Невозможно включить {cls.name}, т.к. {depends_event}')
            else:
                red.hset(cls.key_to_server, cls.name, str(value))
                print(f'{cls.name} = {value}')
        else:
            red.hset(cls.key_to_server, cls.name, str(value))
            print(f'{cls.name} = {value}')

    @classmethod
    def leak(cls, value):
        if value:
            red.hset(cls.key_to_server, cls.name, cls.OFF)
            print(f'Протечка, {cls.name} - False')
        else:
            print(f'Протечка устранена, {cls.name}')


class ColdWater(Controls):
    name = Events.cold_water.name
    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
            cls.leak(value)

        if event == cls.name:
            cls.switch(value, Events.bedroom_presence.name)


class HotWater(Controls):
    name = Events.hot_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
            cls.leak(value)

        if event == cls.name:
            cls.switch(value, Events.bedroom_presence.name)


class Boiler(Controls):
    name = Events.boiler.name
    DEPENDS = {Events.cold_water.name: 'True'}

    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
            '''
            ПРОСТО ПЕРЕД ВЫЗОВОМ LEAK=FALSE ПРОВЕРЯЕМ ПОКАЗАНИЯ ДЫМА ИЛИ ДРУГИХ ЗАВИСИМОСТЕЙ
            '''

            cls.leak(value)



class WashingMachine(Controls):
    name = Events.washing_machine.name
    ON = 'on'
    OFF = 'off'
    BLOCK = 'broken'
    DEPENDS = {Events.cold_water.name: 'True'}

    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
            cls.leak(value)


class AirConditioner(Controls):
    @classmethod
    def update(cls, event):
        pass


class BedroomLight(Controls):
    @classmethod
    def update(cls, event):
        pass


class BathroomLight(Controls):
    @classmethod
    def update(cls, event):
        pass


class Curtains(Controls):
    @classmethod
    def update(cls, event):
        pass

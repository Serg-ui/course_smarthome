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
    def switch_on(cls):
        red.hset(cls.key_to_server, cls.name, cls.ON)
        print(f'{cls.name} - Включен')

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
            if not value:
                cls.switch_on()
            cls.leak(value)

        if event == cls.name:
            pass


class HotWater(Controls):
    name = Events.hot_water.name

    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
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
        if event == Events.bedroom_presence.name:
            if not value:
                if red.hget(cls.key_controls, Events.smoke_detector.name) == 'False':
                    cls.switch_on()
                else:
                    print('Невозможно вкл бойлер из-за задымления')

            cls.leak(value)

        if event == Events.cold_water.name:
            if not value:
                red.hset(cls.key_to_server, cls.name, cls.OFF)
                print('Бойлер выключен из-за перекрытия холодной воды')

        if event == cls.name:
            if value:
                water = red.hget(cls.key_controls, Events.cold_water.name)
                smoke = red.hget(cls.key_controls, Events.smoke_detector.name)
                leak = red.hget(cls.key_controls, Events.leak_detector.name)

                if water == 'True' and smoke == 'False' and leak == 'False':
                    red.hset(cls.key_to_server, cls.name, cls.ON)
                    print('Бойлер вкл')
            else:
                red.hset(cls.key_to_server, cls.name, cls.OFF)
                print('Бойлер выкл')

class WashingMachine(Controls):
    name = Events.washing_machine.name
    ON = 'on'
    OFF = 'off'
    BLOCK = 'broken'
    DEPENDS = {Events.cold_water.name: 'True'}

    @classmethod
    def update(cls, event, value):
        if event == Events.bedroom_presence.name:
            if not value:
                if red.hget(cls.key_controls, Events.smoke_detector.name) == 'False':
                    cls.switch_on()
                else:
                    print('Невозможно вкл cт. машину из-за задымления')

            cls.leak(value)

        if event == Events.cold_water.name:
            if not value:
                red.hset(cls.key_to_server, cls.name, cls.OFF)
                print('Стиральная машина выключена из-за перекрытия холодной воды')

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

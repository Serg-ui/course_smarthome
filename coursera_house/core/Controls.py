from abc import ABC, abstractmethod
from .Events import *
from django.core.mail import send_mail


class Controls(ABC):
    status = ''
    block = False

    def __init__(self, status, **kwargs):
        self.status = status

    @classmethod
    def switch(cls, status: bool):
        cls.status = status

    @classmethod
    def broken(cls, status: bool):
        cls.block = status

    @abstractmethod
    def update(self, event, value):
        pass


class ColdWater(Controls):
    @classmethod
    def update(cls, event, value):
        if event == Events.smoke_detector.name:
            if value:
                cls.status = False
                cls.block = True
                cls.leak = True
                print('Протечка, холодная вода выкл')
            else:
                cls.block = False
                cls.leak = False
                print('Протечка устранена, холодная вода')



class HotWater(Controls):
    @classmethod
    def update(cls, event, value):
        if event == Events.smoke_detector.name:
            if value:
                cls.status = False
                cls.block = True
                print('Протечка, горячая вода выкл')
            else:
                cls.block = False
                print('Протечка устранена, горячая вода')


class Boiler(Controls):
    @classmethod
    def update(cls, event, value):
        if event == Events.smoke_detector.name:
            if value:
                cls.status = False
                cls.block = True
                print('Протечка, бойлер выкл')
            else:
                cls.block = False
                print('Протечка устранена, бойлер блокировка снята')


class WashingMachine(Controls):
    @classmethod
    def update(cls, event, value):
        if event == Events.smoke_detector.name:
            if value:
                cls.status = False
                cls.block = True
                print('Протечка, стриальная машина выкл и заблокирована')
            else:
                cls.block = False
                print('Протечка устранена, стриальная машина блокировка снята')


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

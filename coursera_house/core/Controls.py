from abc import ABC, abstractmethod


class Controls(ABC):
    status = False
    is_broken = False

    def __init__(self):
        pass

    @classmethod
    def switch(cls, status: bool):
        cls.status = status

    @classmethod
    def broken(cls, status: bool):
        cls.is_broken = status

    @abstractmethod
    def update(self, event):
        pass


class ColdWater(Controls):
    @classmethod
    def update(cls, event):
        pass


class HotWater(Controls):
    @classmethod
    def update(cls, event):
        pass


class Boiler(Controls):
    @classmethod
    def update(cls, event):
        pass


class WashingMachine(Controls):
    @classmethod
    def update(cls, event):
        pass


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

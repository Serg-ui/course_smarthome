from enum import Enum

FLAGS = {
    'water_leak': False
}


class Events(Enum):
    leak_detector = 1
    cold_water = 2
    water_temp = 3
    curtains_manual_mode = 4
    outdoor_dark = 5
    outdoor_light_or_bedroom_light_on = 6
    smoke_detector = 7
    bedroom_temp = 8


class Notifier:
    subscribers = {event: set() for event in [event.name for event in Events]}

    @classmethod
    def get_subscribers(cls, event):
        return cls.subscribers[event]

    @classmethod
    def subscribe(cls, event, who: list):
        for sub in who:
            cls.subscribers[event].add(sub)

    @classmethod
    def unsubscribe(cls, event, who):
        cls.subscribers[event].discard(who)

    @classmethod
    def dispatch(cls, event, value):
        for subscriber in cls.get_subscribers(event):
            subscriber.update(event, value)

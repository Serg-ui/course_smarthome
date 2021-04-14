from enum import Enum

FLAGS = {
    'water_leak': False
}

class Events(Enum):
    water_leak = 1
    cold_water_off = 2
    hot_water_temp = 3
    curtains_manual_mode = 4
    outdoor_dark = 5
    outdoor_light_or_bedroom_light_on = 6
    smoke = 7
    bedroom_temp = 8


class Notifier:
    def __init__(self):
        self._subscribers = {event: set() for event in [event.name for event in Events]}

    def get_subscribers(self, event):
        return self._subscribers[event]

    def subscribe(self, event, who):
        self._subscribers[event].add(who)

    def unsubscribe(self, event, who):
        self._subscribers[event].discard(who)

    def dispatch(self, event):
        for subscriber in self.get_subscribers(event):
            subscriber.update(event)







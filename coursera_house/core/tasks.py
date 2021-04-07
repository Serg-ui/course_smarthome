from celery import shared_task
from celery.task import periodic_task
from celery.schedules import crontab
from datetime import timedelta


@periodic_task(run_every=(timedelta(seconds=1)), name='first')
def first():
    print('hello')

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)



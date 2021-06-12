from django.db import models


# Create your models here.
class Setting(models.Model):
    controller_name = models.CharField(max_length=40, unique=True)
    label = models.CharField(max_length=100)
    value = models.IntegerField(default=20)

    @classmethod
    def safe_get(cls, name):
        try:
            go = Setting.objects.get(controller_name=name).value
        except Setting.DoesNotExist:
            go = None

        return go
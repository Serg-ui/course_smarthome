from django import forms
from .models import Setting


class ControllerForm(forms.Form):
    bedroom_target_temperature = forms.IntegerField(required=True,
                                                    min_value=16,
                                                    max_value=50,
                                                    initial=Setting.objects.get(controller_name='bedroom_target_temperature').value)
    hot_water_target_temperature = forms.IntegerField(required=True,
                                                      min_value=24,
                                                      max_value=90,
                                                      initial=Setting.objects.get(controller_name='hot_water_target_temperature').value)
    bedroom_light = forms.BooleanField(required=False,
                                       initial=bool(Setting.objects.get(controller_name='bedroom_light').value))
    bathroom_light = forms.BooleanField(required=False,
                                        initial=bool(Setting.objects.get(controller_name='bathroom_light').value))

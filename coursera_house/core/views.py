import json

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, View
import requests
from django.conf import settings
from .models import Setting
from .form import ControllerForm
from django.forms.models import model_to_dict


class ControllerView(View):
    def get_data(self):
        air_temp = Setting.objects.get(controller_name='bedroom_target_temperature').value
        water_temp = Setting.objects.get(controller_name='hot_water_target_temperature').value
        return {'bedroom_target_temperature': air_temp, 'hot_water_target_temperature': water_temp}

    def get_data_from_server(self):
        try:
            data = requests.get(settings.SMART_HOME_API_URL,
                                headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
        except requests.exceptions.RequestException:
            return 'error'

        if data.status_code != 200:
            return 'error'

        try:
            data_json = data.json()
        except json.JSONDecodeError:
            return 'error'

        return {k['name']: k['value'] for k in data_json['data']}

    def get(self, request):

        data = self.get_data_from_server()
        if data == 'error':
            return HttpResponse('bad gateway', status=502)

        form_data = self.get_data()
        form_data['bedroom_light'] = data['bedroom_light']
        form_data['bathroom_light'] = data['bathroom_light']

        form = ControllerForm(form_data)

        return render(request, 'core/control.html', {'form': form, 'data': data})

    def post(self, request):
        form = ControllerForm(request.POST)
        data = {}

        if form.is_valid():
            data = self.get_data_from_server()
            if data == 'error':
                return HttpResponse('bad gateway', status=502)

            clean = form.cleaned_data

            Setting.objects.filter(controller_name='bedroom_target_temperature').update(
                value=clean['bedroom_target_temperature'])
            Setting.objects.filter(controller_name='hot_water_target_temperature').update(
                value=clean['hot_water_target_temperature'])

        return render(request, 'core/control.html', {'form': form, 'data': data})


class ControllerView2(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')

    def get_context_data(self, **kwargs):
        context = super(ControllerView2, self).get_context_data()

        data = requests.get(settings.SMART_HOME_API_URL,
                            headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})

        data = data.json()

        context['data'] = {k['name']: k['value'] for k in data['data']}
        return context

    def get_initial(self):
        return {
            'bedroom_target_temperature': Setting.safe_get('bedroom_target_temperature'),
            'hot_water_target_temperature': Setting.objects.get(controller_name='hot_water_target_temperature').value,
            'bedroom_light': bool(Setting.objects.get(controller_name='bedroom_light').value),
            'bathroom_light': bool(Setting.objects.get(controller_name='bathroom_light').value)
        }

    def form_valid(self, form):
        o = Setting.objects.all()

        o.filter(controller_name='bedroom_target_temperature'). \
            update(value=form.__getitem__('bedroom_target_temperature').value())
        o.filter(controller_name='hot_water_target_temperature'). \
            update(value=form.__getitem__('hot_water_target_temperature').value())
        o.filter(controller_name='bedroom_light'). \
            update(value=int(form.__getitem__('bedroom_light').value()))
        o.filter(controller_name='bathroom_light'). \
            update(value=int(form.__getitem__('bathroom_light').value()))

        return super(ControllerView2, self).form_valid(form)

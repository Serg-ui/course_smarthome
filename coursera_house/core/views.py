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
    def get_data_from_server(self):

        data = requests.get(settings.SMART_HOME_API_URL,
                            headers={'authorization': f'Bearer {settings.SMART_HOME_ACCESS_TOKEN}'})
        data_json = data.json()

        if data.status_code != 200:
            raise requests.exceptions.RequestException

        return {k['name']: k['value'] for k in data_json['data']}


    def get(self, request):

        form = ControllerForm()
        try:
            data = self.get_data_from_server()
        except requests.exceptions.RequestException:
            return HttpResponse('bad gateway', status=502)

        return render(request, 'core/control.html', {'form': form, 'data': data})

    def post(self, request):
        form = ControllerForm(request.POST)

        try:
            data = self.get_data_from_server()
        except requests.exceptions.RequestException:
            return HttpResponse('bad gateway', status=502)

        if form.is_valid():
            clean = form.cleaned_data

            Setting.objects.filter(controller_name='bedroom_target_temperature').update(
                value=clean['bedroom_target_temperature'])
            Setting.objects.filter(controller_name='hot_water_target_temperature').update(
                value=clean['hot_water_target_temperature'])
            Setting.objects.filter(controller_name='bedroom_light').update(
                value=clean['bedroom_light'])
            Setting.objects.filter(controller_name='bathroom_light').update(
                value=clean['bathroom_light'])

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

        o.filter(controller_name='bedroom_target_temperature').\
            update(value=form.__getitem__('bedroom_target_temperature').value())
        o.filter(controller_name='hot_water_target_temperature').\
            update(value=form.__getitem__('hot_water_target_temperature').value())
        o.filter(controller_name='bedroom_light').\
            update(value=int(form.__getitem__('bedroom_light').value()))
        o.filter(controller_name='bathroom_light').\
            update(value=int(form.__getitem__('bathroom_light').value()))

        return super(ControllerView2, self).form_valid(form)

from django.urls import reverse_lazy
from django.views.generic import FormView
import requests
from django.conf import settings
from .models import Setting
from .form import ControllerForm
from .tasks import smart_home_manager


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()

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

        return super(ControllerView, self).form_valid(form)

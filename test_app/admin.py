from django.contrib import admin
from django.http import JsonResponse
from django.urls import reverse_lazy

from django_reaction.admin import AlpineAdminMixin
from django_reaction.rule import Rule, Field
from test_app.models import Task, Country, City


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(AlpineAdminMixin, admin.ModelAdmin):

    @property
    def reaction_rules(self):
        return [
            Rule().when(Field('engine').value == 'engine_a').show(Field('params')),
            Rule().map_to(Field('params'), Field('engine'), {
                'engine_a': '{"mode": "fast"}',
                'engine_b': '{"mode": "slow"}'
            }),
            Rule().fetch(reverse_lazy('admin:myapp_mymodel_custom'), Field('description'), Field('engine')),
            Rule().when(Field('is_active').value == True).show(Field('description'))
        ]

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        my_urls = [path(
            'get-engine-config/',
            self.admin_site.admin_view(self.my_custom_view),
            name='myapp_mymodel_custom'
        )]
        return my_urls + urls

    def my_custom_view(self, request):
        return JsonResponse({"1":"2"})

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from apps.b3_migration.models.switch import Switch
from apps.b3_organization.models.organization import Organization


def switch_on(modeladmin, request, queryset):
    queryset.update(active=True)


def switch_off(modeladmin, request, queryset):
    queryset.update(active=False)


switch_on.short_description = "Turn on all selected Switches"
switch_off.short_description = "Turn off all selected Switches"


@admin.register(Switch)
class SwitchAdmin(admin.ModelAdmin):
    change_list_template = "b3_migration/switch_changelist.html"
    list_display = (
        'feature',
        'organization',
        'site',
        'active',
    )
    list_filter = ('active', )
    search_fields = (
        'feature',
        'organization__site__name',
        'organization__showname',
        'organization__site__domain',
    )

    def site(self, obj):
        return obj.organization.site

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url('create-all/', self.create_all_switches),
        ]
        return my_urls + urls

    def create_all_switches(self, request):
        for feature in Switch.FEATURE_CHOICES:
            for organization in Organization.objects.all():
                Switch.objects.get_or_create(
                    feature=feature[0], organization=organization
                )
        return HttpResponseRedirect("../")

    actions = [switch_on, switch_off]

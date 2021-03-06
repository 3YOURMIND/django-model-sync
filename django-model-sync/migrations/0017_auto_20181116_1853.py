# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-11-16 18:53
from __future__ import unicode_literals

from django.db import migrations, models


def delete_switches(apps, schema_editor):
    Switch = apps.get_model('b3_migration', 'switch')
    for switch in Switch.objects.all():
        if switch.feature == 'new_checkout':
            switch.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('b3_migration', '0016_auto_20181101_1311'),
    ]

    operations = [
        migrations.RunPython(delete_switches, migrations.RunPython.noop, atomic=True),
        migrations.RemoveField(
            model_name='switch',
            name='name',
        ),
        migrations.AlterField(
            model_name='switch',
            name='feature',
            field=models.CharField(choices=[('new_user_panel', 'New UserPanel'), ('left_navigation', 'Left Navigation')], help_text='Feature being switched/toggled', max_length=32, verbose_name='Feature'),
        ),
    ]

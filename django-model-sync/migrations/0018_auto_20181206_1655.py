# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-06 16:55
from __future__ import unicode_literals

from django.db import migrations, models

def delete_switches(apps, schema_editor):
    Switch = apps.get_model('b3_migration', 'switch')
    for switch in Switch.objects.all():
        if switch.feature == 'left_navigation':
            switch.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('b3_migration', '0017_auto_20181116_1853'),
    ]

    operations = [
        migrations.RunPython(delete_switches, migrations.RunPython.noop, atomic=True),
        migrations.AlterField(
            model_name='switch',
            name='feature',
            field=models.CharField(choices=[('new_user_panel', 'New UserPanel')], help_text='Feature being switched/toggled', max_length=32, verbose_name='Feature'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-29 14:17
from __future__ import unicode_literals

from django.db import migrations, models
from django_migration_linter.operations import IgnoreMigration


class Migration(migrations.Migration):

    dependencies = [
        ('b3_migration', '0009_migrate_shipping_methods'),
    ]

    operations = [
        IgnoreMigration(),
        migrations.AlterField(
            model_name='switch',
            name='name',
            field=models.CharField(help_text='Switch name', max_length=128, null=True, verbose_name='Name'),
        ),
    ]

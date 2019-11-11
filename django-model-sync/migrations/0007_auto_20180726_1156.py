# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-26 11:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('b3_migration', '0006_merge_20180725_1313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='switch',
            name='feature',
            field=models.CharField(choices=[('new_checkout', 'New Checkout'), ('new_pricing', 'New Pricing'), ('new_payment_methods', 'New Payment Methods')], help_text='Feature being switched/toggled', max_length=32, verbose_name='Feature'),
        ),
    ]

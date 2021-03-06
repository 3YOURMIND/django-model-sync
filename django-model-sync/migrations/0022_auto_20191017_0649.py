# Generated by Django 2.1.13 on 2019-10-17 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('b3_migration', '0021_auto_20190926_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='switch',
            name='feature',
            field=models.CharField(choices=[('new_user_panel', 'New UserPanel'), ('new_basket', 'New Basket'), ('sales_transaction', 'Sales Transaction'), ('part_requirements', 'Part Requirements')], help_text='Feature being switched/toggled', max_length=32, verbose_name='Feature'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-26 02:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monkey', '0002_auto_20171125_2303'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='tk',
        ),
        migrations.AddField(
            model_name='token',
            name='user',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to='monkey.Account'),
            preserve_default=False,
        ),
    ]

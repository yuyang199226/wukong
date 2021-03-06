# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-25 15:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monkey', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_value', models.CharField(max_length=64, verbose_name='令牌')),
            ],
        ),
        migrations.AddField(
            model_name='account',
            name='tk',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='monkey.Token'),
        ),
    ]

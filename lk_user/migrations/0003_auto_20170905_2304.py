# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 23:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
        ('lk_user', '0002_auto_20170905_2255'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lkuser',
            name='team_id',
        ),
        migrations.AddField(
            model_name='lkuser',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='team', to='project.Team', verbose_name='\u041a\u043e\u043c\u0430\u043d\u0434\u0430'),
        ),
    ]
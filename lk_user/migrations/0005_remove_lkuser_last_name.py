# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-18 20:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lk_user', '0004_lkuser_avatar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lkuser',
            name='last_name',
        ),
    ]

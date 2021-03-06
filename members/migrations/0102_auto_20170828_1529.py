# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-08-28 13:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0101_activity_member_justified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='member_justified',
            field=models.BooleanField(default=True, help_text='Bestemmer om personerne bliver til medlemmer i forhold til DUF. De fleste aktiviteter er sæsoner og medlemsberettiget. Hvis du er i tvivl, så spørg på Slack i #medlemsssystem-support.', verbose_name='Aktiviteten gør personen til medlem'),
        ),
    ]

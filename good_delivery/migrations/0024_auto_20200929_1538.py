# Generated by Django 3.1.1 on 2020-09-29 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('good_delivery', '0023_auto_20200928_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='gooddelivery',
            name='num_documento',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='gooddelivery',
            name='tipo_documento',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

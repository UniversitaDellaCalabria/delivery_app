# Generated by Django 3.1.1 on 2020-09-28 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('good_delivery', '0020_auto_20200928_0838'),
    ]

    operations = [
        migrations.AddField(
            model_name='gooddelivery',
            name='disabled_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='disabled_point', to='good_delivery.deliverypoint'),
        ),
        migrations.AddField(
            model_name='gooddelivery',
            name='returned_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='returned_point', to='good_delivery.deliverypoint'),
        ),
    ]

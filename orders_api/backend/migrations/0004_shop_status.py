# Generated by Django 4.2 on 2023-04-20 21:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_alter_shop_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]

# Generated by Django 4.2.4 on 2023-08-22 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Models', '0005_message_photo_receipts_user_use_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='max_summ',
            field=models.IntegerField(default=0, verbose_name='Максимальное колличество услуг'),
        ),
        migrations.AddField(
            model_name='product',
            name='min_summ',
            field=models.IntegerField(default=0, verbose_name='Минимальное колличество услуг'),
        ),
    ]

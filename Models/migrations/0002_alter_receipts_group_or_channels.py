# Generated by Django 4.2.4 on 2023-08-18 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Models', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipts',
            name='group_or_channels',
            field=models.ManyToManyField(blank=True, null=True, to='Models.groupandchennel', verbose_name='Группы и чаты для проверки'),
        ),
    ]
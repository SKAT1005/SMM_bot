# Generated by Django 4.2.4 on 2023-08-20 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Models', '0004_user_command_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фотография к сообщению'),
        ),
        migrations.AddField(
            model_name='receipts',
            name='user_use',
            field=models.ManyToManyField(related_name='use_user', to='Models.user', verbose_name='Пользователи, использовавшие чек'),
        ),
        migrations.AlterField(
            model_name='message',
            name='message',
            field=models.CharField(max_length=1024, verbose_name='Сообщение'),
        ),
    ]

# Generated by Django 3.2.13 on 2022-05-13 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_rename_created_subscribe_add_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='measurement_unit',
            field=models.CharField(help_text='Введите еденицу измерения', max_length=150, verbose_name='Еденица измерения'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(help_text='Введите название ингредиента', max_length=150, verbose_name='Название ингредиента'),
        ),
    ]

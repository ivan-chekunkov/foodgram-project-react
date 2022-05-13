# Generated by Django 3.2.13 on 2022-05-13 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20220513_2340'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'ordering': ['-add_date'], 'verbose_name': 'Покупка в корзине', 'verbose_name_plural': 'Покупки в корзине'},
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='add_date',
            field=models.DateTimeField(auto_now_add=True, default='2022-02-02 22:22', verbose_name='Дата добавления'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='recipe',
            field=models.ManyToManyField(related_name='shopping_cart', to='recipes.Recipe', verbose_name='Рецепт'),
        ),
    ]
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название тега',
        help_text='Введите название тега',
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='Цвет тега в формате HEX-кода',
        help_text='Введите цвет тега в формате HEX-кода',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Уникальный слаг',
        help_text='Введите уникальный слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=150,
        verbose_name='Еденица измерения',
        help_text='Введите еденицу измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}: {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipe',
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    image = models.ImageField(
        verbose_name='Картинка к рецепту',
        help_text='Выберите картинку',
        upload_to='static/recipe/',
        blank=True,
        null=True,
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Опишите рецепт',
    )
    tags = models.ManyToManyField(
        to=Tag,
        related_name='recipe',
        verbose_name='Теги рецепта',
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='AmountOfIngredients',
        verbose_name='Ингредиенты',
        help_text='Введите название ингредиентов и их количество',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        default=1,
        help_text='Введите время приготовления в минутах',
        validators=[MinValueValidator(
            1,
            message='Время приготовления не может быть меньше одной минуты')],
    )
    pud_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pud_date']

    def __str__(self):
        return f'{self.name}: {self.text[:50]}...'


class AmountOfIngredients(models.Model):
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Название ингредиента',
        help_text='Поле связанное с ингредиентом',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Название рецепта',
        help_text='Поле связанное с рецептом',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        default=1,
        validators=[MinValueValidator(
            1,
            message='Значение не может быть меньше еденицы')],
    )

    class Meta:
        verbose_name = 'Количество ингредиента для конкретного рецепта'
        verbose_name_plural = 'Количество ингредиентов для конкретного рецепта'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient',),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} используется в рецепте {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping',
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Покупка в корзине'
        verbose_name_plural = 'Покупки в корзине'
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_shopping'),
        ]

    def __str__(self):
        return f'У {self.user} {self.recipe} находиться в списке покупок'


class Favorite(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='fovorite',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='fovorite',
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-add_date']
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_favorite'),
        ]

    def __str__(self):
        return f'У {self.user} {self.recipe} находиться в избранном'

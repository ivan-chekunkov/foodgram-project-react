from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator
from django.dispatch import receiver

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=150,
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


class Tag(models.Model):
    name = models.CharField(
        'Имя',
        max_length=60,
        unique=True)
    color = models.CharField(
        'Цвет',
        max_length=7,
        unique=True)
    slug = models.SlugField(
        'Ссылка',
        max_length=100,
        unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


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
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        help_text='Введите название ингредиентов и их количество',
    )
    tags = models.ManyToManyField(
        to=Tag,
        verbose_name='Теги рецепта',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        default=1,
        help_text='Введите время приготовления в минутах',
        validators=[MinValueValidator(
            1,
            message='Мин. время приготовления 1 минута'), ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return f'{self.name}: {self.text[:50]}...'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Название рецепта',
        help_text='Поле связанное с рецептом',
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Название ингредиента',
        help_text='Поле связанное с ингредиентом',
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


class Subscribe(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class FavoriteRecipe(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Пользователь'
    )
    recipe = models.ManyToManyField(
        to=Recipe,
        related_name='favorite_recipe',
        verbose_name='Рецепт',
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-add_date']

    def __str__(self):
        return f'У {self.user} {self.recipe} находиться в избранном'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(
            sender, instance, created, **kwargs):
        if created:
            return FavoriteRecipe.objects.create(user=instance)


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
        null=True,
    )
    recipe = models.ManyToManyField(
        to=Recipe,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Покупка в корзине'
        verbose_name_plural = 'Покупки в корзине'
        ordering = ['-add_date']

    def __str__(self):
        return f'У {self.user} {self.recipe} находиться в списке покупок'

    @receiver(post_save, sender=User)
    def create_shopping_cart(
            sender, instance, created, **kwargs):
        if created:
            return ShoppingCart.objects.create(user=instance)

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    username = models.CharField(
        blank=False,
        unique=True,
        max_length=150,
        verbose_name='Никнейм пользователя',
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        max_length=254,
        verbose_name='Электронная почта',
    )
    first_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Фамилия',
    )
    password = models.CharField(
        blank=False,
        max_length=150,
        verbose_name='Пароль',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            UniqueConstraint(fields=['email', ], name='email'),
            UniqueConstraint(fields=['username', ], name='username')
        ]

    def __str__(self):
        return f'{self.username}'


class Follow(models.Model):
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
            UniqueConstraint(
                fields=('user', 'author',),
                name='unique_follow'),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

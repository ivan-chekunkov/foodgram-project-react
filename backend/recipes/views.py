from rest_framework.decorators import action, api_view
import io

from rest_framework import viewsets
from .serializers import (RecipeReadSerializer, ShortRecipeSerializer,
                          TagSerializer, IngredientSerializer,
                          SubscriptionSerializer, RecipeWriteSerializer,
                          UserListSerializer, UserCreateSerializer,
                          UserSetPassword)
from .models import Recipe, Tag, Ingredient, Favorite, ShoppingCart
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from djoser.views import UserViewSet
from users.models import Follow
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth import get_user_model
from .permissions import IsAuthorOrAdminOrReadOnly
from django.db import IntegrityError
from .mixins import PermissionAndPaginationMixin
from .filters import RecipeFilter
from django.db.models.expressions import Exists, OuterRef, Value
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.contrib.auth.hashers import make_password
from django.http import FileResponse
from django.db.models.aggregates import Sum
from django.http import Http404, HttpResponse
User = get_user_model()

FILENAME = 'shoppingcart.pdf'


class TagsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    Получение списка тегов или отдельного тега.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    Получение списка ингредиентов или отдельного ингредиента.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class CustomUsersViewSet(UserViewSet):
    """
    Класс для эндпоинтов работы с пользователями.
    """
    serializer_class = UserListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.annotate(
            is_subscribed=Exists(
                self.request.user.follower.filter(
                    author=OuterRef('id'))
            )).prefetch_related(
                'follower', 'following'
        ) if self.request.user.is_authenticated else User.objects.annotate(
            is_subscribed=Value(False))

    def get_serializer_class(self):
        if self.request.method.lower() == 'POST':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False, methods=['GET', ],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """
        Получить на кого пользователь подписан.
        """

        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)

    def create_subscribe(self, request, author):
        """
        Подписаться на пользователя.
        """

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            subscribe = Follow.objects.create(
                user=request.user,
                author=author,
            )
        except IntegrityError:
            return Response(
                {'errors': 'Нельзя подписаться дважды'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SubscriptionSerializer(
            subscribe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscribe(self, request, author):
        """
        Отписаться от пользователя.
        """

        try:
            Follow.objects.get(user=request.user, author=author).delete()
        except Follow.DoesNotExist:
            return Response(
                {'errors': 'Нельзя отписаться от данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, id=None):
        """
        Подписка на пользователя и отписка от пользователя.
        """

        try:
            author = get_object_or_404(User, pk=id)
        except Http404:
            return Response(
                {'detail': 'Несуществующий пользователь'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.create_subscribe(request, author)
        return self.delete_subscribe(request, author)

    @action(
        methods=['POST', ],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='set_password',
    )
    def set_password(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Вы не авторизованы!'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSetPassword(
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Пароль изменен!'},
                status=status.HTTP_201_CREATED)
        return Response(
            {'error': 'Введите верные данные!'},
            status=status.HTTP_400_BAD_REQUEST)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeReadSerializer(
            instance=serializer.instance,
            context={'request': self.request},
        )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def create_favorite(self, request, recipe):
        """
        Добавить рецепт в избранное.
        """

        try:
            favorite = Favorite.objects.create(
                user=request.user,
                recipe=recipe,
            )
        except IntegrityError:
            return Response(
                {'errors': 'Нельзя добавить в избранное дважды'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ShortRecipeSerializer(
            favorite.recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorite(self, request, recipe):
        """
        Убрать рецепт из избранного.
        """

        try:
            Favorite.objects.get(user=request.user, recipe=recipe).delete()
        except Favorite.DoesNotExist:
            return Response(
                {'errors': 'Нельзя убрать из избранного'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """
        Подписка на пользователя и отписка от пользователя.
        """

        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                {'detail': 'Несуществующий рецепт'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.create_favorite(request, recipe)
        return self.delete_favorite(request, recipe)

    def add_to_shopping_cart(self, request, recipe):
        try:
            add_recipe = ShoppingCart.objects.create(
                user=request.user,
                recipe=recipe,
            )
        except IntegrityError:
            return Response(
                {'errors': 'Нельзя добавить в избранное дважды'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ShortRecipeSerializer(
            add_recipe.recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_shopping_cart(self, request, recipe):
        try:
            ShoppingCart.objects.get(user=request.user, recipe=recipe).delete()
        except ShoppingCart.DoesNotExist:
            return Response(
                {'errors': 'Нельзя убрать из избранного'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                {'detail': 'Несуществующий рецепт'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.add_to_shopping_cart(request, recipe)
        return self.remove_from_shopping_cart(request, recipe)

    NAME = 'ingredients__ingredient__name'
    MEASUREMENT_UNIT = 'ingredients__ingredient__measurement_unit'

    def generate_shopping_cart_data(self, request):
        print('-'*20)
        print(request.user.shopping_cart.prefetch_related('recipe'))
        print('-'*20)
        recipes = (
            request.user.shopping_cart.prefetch_related('recipe')
        )
        print(recipes[0].recipe.amount_ingredients.prefetch_related(
            'ingredient'))
        print('-'*20)
        return (
            recipes.recipe.order_by(self.NAME)
            .values(self.NAME, self.MEASUREMENT_UNIT)
            .annotate(total=Sum('ingredients__amount'))
        )

    def generate_ingredients_content(self, ingredients):
        content = ''
        for ingredient in ingredients:
            content += (
                f'{ingredient[self.NAME]}'
                f' ({ingredient[self.MEASUREMENT_UNIT]})'
                f' — {ingredient["total"]}\r\n'
            )
        return content

    @action(detail=False)
    def download_shopping_cart(self, request):
        try:
            ingredients = self.generate_shopping_cart_data(request)
        except ShoppingCart.DoesNotExist:
            return Response(
                {'errors': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )
        content = self.generate_ingredients_content(ingredients)
        response = HttpResponse(
            content, content_type='text/plain,charset=utf8'
        )
        response['Content-Disposition'] = f'attachment; filename={FILENAME}'
        return response

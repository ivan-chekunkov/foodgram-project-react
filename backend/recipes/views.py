from django.contrib.auth import get_user_model, hashers
from django.db import IntegrityError
from django.db.models import Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from foodgram.settings import URL_PATH
from .filters import RecipeFilter
from .mixins import PermissionAndPaginationMixin
from .models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                     Subscribe, Tag)
from .permissions import IsAuthenticated, IsAuthorOrAdminOrReadOnly
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, ShortRecipeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserCreateSerializer, UserListSerializer,
                          UserSetPasswordSerializer)

User = get_user_model()

CONSTANT_KEY_MSG = {
    'NOT_SUB_TO_YOURSELF': {'errors': 'Нельзя подписаться на себя'},
    'NOT_SUB_TO_TWICE': {'errors': 'Нельзя подписаться дважды'},
    'NOT_SUB_DELETE': {'errors': 'Нельзя отписаться от данного пользователя'},
    'USER_NOT_FOUND': {'detail': 'Несуществующий пользователь!'},
    'PASSWORD_OK': {'message': 'Пароль изменен!'},
    'NOT_RECIPE': {'detail': 'Несуществующий рецепт'},
    'NOT_FAVORITE_TO_TWICE': {'errors': 'Нельзя добавить в избранное дважды'},
    'NOT_FAVORITE_DELETE': {'errors': 'Нельзя убрать из избранного'},
    'NOT_SHOP_TO_TWICE': {'errors': 'Нельзя добавить в корзину дважды'},
    'NOT_SHOP_DELETE': {'errors': 'Нельзя убрать из корзины'},
    'SHOPPING_CART_EMPTY': {'errors': 'Корзина пуста'},
}

SHOPPING_CATR_FILENAME = 'shoppingcart.txt'


class CustomUsersViewSet(UserViewSet):
    """
    Класс для эндпоинтов работы с пользователями.
    """

    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            is_subscribed = Exists(
                self.request.user.follower.filter(author=OuterRef('id')))
            return User.objects.annotate(
                is_subscribed=is_subscribed
            ).prefetch_related('follower', 'following')
        return User.objects.annotate(is_subscribed=Value(False))

    def get_serializer_class(self):
        if self.request.method.lower() == 'POST':
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        password_field = self.request.data.get('password')
        password = hashers.make_password(password_field)
        serializer.save(password=password)

    @action(
        detail=False, methods=['GET', ],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """
        Получить на кого пользователь подписан.
        """

        user = request.user
        queryset = Subscribe.objects.filter(user=user)
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
                CONSTANT_KEY_MSG['NOT_SUB_TO_YOURSELF'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            subscribe = Subscribe.objects.create(
                user=request.user,
                author=author,
            )
        except IntegrityError:
            return Response(
                CONSTANT_KEY_MSG['NOT_SUB_TO_TWICE'],
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
            Subscribe.objects.get(user=request.user, author=author).delete()
        except Subscribe.DoesNotExist:
            return Response(
                CONSTANT_KEY_MSG['NOT_SUB_DELETE'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
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
                CONSTANT_KEY_MSG['USER_NOT_FOUND'],
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.create_subscribe(request, author)
        return self.delete_subscribe(request, author)

    @action(
        methods=['POST', ],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='set_password',
    )
    def set_password(self, request):
        """
        Смена пароля пользователя на новый.
        """

        serializer = UserSetPasswordSerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                CONSTANT_KEY_MSG['PASSWORD_OK'],
                status=status.HTTP_201_CREATED)


class IngredientsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    Получение списка ингредиентов или отдельного ингредиента.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    """
    Получение списка рецептов или отдельного рецепта.
    Создание, редактирование и удаление рецепта.
    Работа с избранными рецептами и корзиной покупок.
    """

    queryset = Recipe.objects.all()
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

        if FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                CONSTANT_KEY_MSG['NOT_FAVORITE_TO_TWICE'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.favorite_recipe.recipe.add(recipe)
        serializer = ShortRecipeSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorite(self, request, recipe):
        """
        Убрать рецепт из избранного.
        """

        if not FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                CONSTANT_KEY_MSG['NOT_FAVORITE_DELETE'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.favorite_recipe.recipe.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """
        Добавление и удаление рецепта из избранного.
        """

        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                CONSTANT_KEY_MSG['NOT_RECIPE'],
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.create_favorite(request, recipe)
        return self.delete_favorite(request, recipe)

    def add_to_shopping_cart(self, request, recipe):
        """
        Добавление рецептов в список покупок.
        """

        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                CONSTANT_KEY_MSG['NOT_SHOP_TO_TWICE'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.shopping_cart.recipe.add(recipe)
        serializer = ShortRecipeSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_shopping_cart(self, request, recipe):
        """
        Удаление рецептов из списка покупок.
        """

        if not ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                CONSTANT_KEY_MSG['NOT_SHOP_DELETE'],
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.shopping_cart.recipe.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавление и удаление рецептов в список покупок.
        """

        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                CONSTANT_KEY_MSG['NOT_RECIPE'],
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == 'POST':
            return self.add_to_shopping_cart(request, recipe)
        return self.remove_from_shopping_cart(request, recipe)

    def generate_data_shopping_cart(self, request):
        """
        Получение данных для списка покупок.
        """

        return (
            request.user.shopping_cart.recipe.values(
                'ingredients__name',
                'ingredients__measurement_unit'
            )).annotate(amount=Sum('ingredient__amount')).order_by()

    def generate_content_shopping_cart(self, shopping_cart):
        """
        Формирование списка покупок.
        """

        content = '*' * 20 + ' Ваш список покупок ' + '*' * 20 + '\r\n'
        name = 'ingredients__name'
        measurement_unit = 'ingredients__measurement_unit'
        amount = 'amount'
        for ingredient in shopping_cart:
            content += (
                f'{ingredient[name]}'
                f'({ingredient[measurement_unit]})'
                f' —  {ingredient[amount]}\r\n'
            )
        content += 'Благодарим вас за пользование нашим сайтом \r\n'
        content += URL_PATH
        return content

    @ action(
        methods=['GET', ],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """
        Получение файла с списком покупок.
        """

        shopping_cart = self.generate_data_shopping_cart(request)
        if not shopping_cart:
            return Response(
                CONSTANT_KEY_MSG['SHOPPING_CART_EMPTY'],
                status=status.HTTP_400_BAD_REQUEST
            )
        content = self.generate_content_shopping_cart(shopping_cart)
        response = HttpResponse(
            content, content_type='text/plain,charset=utf8'
        )
        response['Content-Disposition'] = (
            f'attachment; filename={SHOPPING_CATR_FILENAME}'
        )
        return response


class TagsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    Получение списка тегов или отдельного тега.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer

from django.contrib.auth import (authenticate, get_user_model, hashers,
                                 password_validation)
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from .mixins import IsSubscribedMixin
from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscribe, Tag)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class UserListSerializer(IsSubscribedMixin, serializers.ModelSerializer):
    """
    Сериализатор для вывода списка пользователей.
    """

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя.
    """

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',)

    def validate_password(self, password):
        password_validation.validate_password(password)
        return password


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для короткого содержимого рецепта в подписках.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок.
    """

    id = serializers.IntegerField(
        source='author.id')
    email = serializers.EmailField(
        source='author.email')
    username = serializers.CharField(
        source='author.username')
    first_name = serializers.CharField(
        source='author.first_name')
    last_name = serializers.CharField(
        source='author.last_name')
    recipes = serializers.SerializerMethodField(
        read_only=True)
    recipes_count = serializers.SerializerMethodField(
        read_only=True)
    is_subscribed = serializers.SerializerMethodField(
        read_only=True)

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'recipes', 'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.author.recipe.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[:int(limit)] if limit
            else obj.author.recipe.all())
        return ShortRecipeSerializer(
            recipes,
            many=True).data


class UserSetPasswordSerializer(serializers.Serializer):
    """
    Сериализатор для смены пароля пользователя.
    """

    new_password = serializers.CharField(
        label='Новый пароль')
    current_password = serializers.CharField(
        label='Текущий пароль')

    def validate_new_password(self, new_password):
        password_validation.validate_password(new_password)
        return new_password

    def validate_current_password(self, current_password):
        request = self.context.get('request')
        if not authenticate(
            username=request.user.email,
            password=current_password
        ):
            raise serializers.ValidationError(
                detail='Неверный пароль',
                code='authenticate'
            )
        return current_password

    def create(self, validated_data):
        user = self.context['request'].user
        new_password = validated_data.get('new_password')
        password = hashers.make_password(new_password)
        user.password = password
        user.save()
        return validated_data


class AmountOfIngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для поля ингредиенты при чтении рецептов.
    """

    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount')


class AmountOfIngredientsWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для поля ингредиенты при создании рецептов.
    """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class AuthorSerializer(IsSubscribedMixin, serializers.ModelSerializer):
    """
    Сериализатор для поля автор при чтении рецептов.
    """

    is_subscribed = serializers.SerializerMethodField(
        read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения рецептов.
    """

    ingredients = AmountOfIngredientsSerializer(
        many=True,
        required=True,
        source='ingredient',
    )
    tags = TagSerializer(
        read_only=True,
        many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True
    )
    author = AuthorSerializer(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return FavoriteRecipe.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(recipe=obj, user=user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и редактирования рецептов.
    """

    ingredients = AmountOfIngredientsWriteSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(
        max_length=None,
        use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'tags', 'ingredients', 'name',
            'image', 'text', 'cooking_time',
        )

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Должен быть хотя бы один тэг для рецепте!'
            )
        for tag in tags:
            id = tag.id
            if not Tag.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    f'Тэга c ID: -> {id} не существует!'
                )
        return tags

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше или равно 1!')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть хотя бы один ингредиент в рецепте!')
        ingredient_list = []
        for ingredient in ingredients:
            id = ingredient['id']
            if not Ingredient.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    f'Ингредиента c ID: -> {id} не существует!'
                )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент в рецепте должен быть уникальным!')
            ingredient_list.append(ingredient)
            amount = int(ingredient.get('amount'))
            if amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше или равно 1!')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            id = ingredient.get('id')
            amount = ingredient.get('amount')
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=id,
                amount=amount, )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.ingredients.clear()
            instance.tags.set(tags)
        return super().update(instance, validated_data)

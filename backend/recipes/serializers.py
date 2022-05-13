from pyexpat import model
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from .models import Recipe, Tag, Ingredient, AmountOfIngredients, ShoppingCart
from drf_base64.fields import Base64ImageField
from users.models import Follow
from django.shortcuts import get_object_or_404
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для короткого содержимого рецепта в подписках.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AmountOfIngredientsSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = AmountOfIngredients
        fields = (
            'id', 'name', 'measurement_unit', 'amount')


class AmountOfIngredientsWriteSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = AmountOfIngredients
        fields = ('id', 'amount')


class TagWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """

    class Meta:
        model = Tag
        fields = ('id',)


class AuthorSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class RecipeWriteSerializer(serializers.ModelSerializer):
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

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент должен быть уникальным!')
            ingredient_list.append(ingredient)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен хотя бы один тэг для рецепта!')
        for tag_name in tags:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэга {tag_name} не существует!')
        return data

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления >= 1!')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Мин. 1 ингредиент в рецепте!')
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента >= 1!')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            AmountOfIngredients.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'), )

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
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)


class RecipeReadSerializer(serializers.ModelSerializer):
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

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.fovorite.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.shopping.filter(recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок
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

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed',
            'recipes', 'recipes_count',
        )


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',)

    def validate_password(self, password):
        password_validation.validate_password(password)
        return password


class UserSetPassword(serializers.Serializer):
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
                detail='Неудалось авторизоваться',
                code='authenticate'
            )
        return current_password

    def create(self, validated_data):
        user = self.context['request'].user
        new_password = validated_data.get('new_password')
        password = make_password(new_password)
        print('fsdfsdf')
        user.password = password
        user.save()
        return validated_data

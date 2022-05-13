from django.contrib import admin

from .models import (
    AmountOfIngredients,
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)


class AmountOfIngredientsAdmin(admin.ModelAdmin):
    list_display = (
        'ingredient',
        'recipe',
        'amount',
    )
    search_fields = ('ingredient', 'recipe',)
    list_filter = ('ingredient', 'recipe',)
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
        'add_date',
    )
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_editable = ('measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'name',
        'image',
        'text',
        'cooking_time',
        'pud_date',
    )
    search_fields = ('author', 'name', 'tags',)
    list_filter = ('author', 'name', 'pud_date',)
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )
    list_editable = ('slug',)
    search_fields = ('name', )
    list_filter = ('name', )
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'add_date',
    )
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe', 'add_date',)
    empty_value_display = '-пусто-'


admin.site.register(AmountOfIngredients, AmountOfIngredientsAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)

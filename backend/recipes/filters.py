from django_filters.rest_framework import (AllValuesMultipleFilter,
                                           BooleanFilter, FilterSet)

from .models import FavoriteRecipe, Recipe, ShoppingCart


class RecipeFilter(FilterSet):

    is_favorited = BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='get_is_in_shopping_cart')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author',)

    def get_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        user = self.request.user
        favorites = FavoriteRecipe.objects.filter(
            user=user).values_list('recipe', flat=True)
        return queryset.filter(
            id__in=(favorites)
        )

    def get_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        user = self.request.user
        purchases = ShoppingCart.objects.filter(
            user=user).values_list('recipe', flat=True)
        return queryset.filter(
            id__in=(purchases)
        )

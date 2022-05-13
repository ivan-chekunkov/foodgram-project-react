from django_filters.rest_framework import (
    AllValuesMultipleFilter,
    BooleanFilter,
    FilterSet
)

from .models import ShoppingCart
from .models import Recipe


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
        favorites = self.request.user.fovorite.all()
        return queryset.filter(
            pk__in=(favorite.recipe.pk for favorite in favorites)
        )

    def get_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        try:
            purchases = (
                self.request.user.shopping.all()
            )
        except ShoppingCart.DoesNotExist:
            return queryset
        return queryset.filter(
            id__in=(purchase.recipe.pk for purchase in purchases)
        )

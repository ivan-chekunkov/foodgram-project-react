from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUsersViewSet, IngredientsViewSet, RecipesViewSet,
                    TagsViewSet)

app_name = 'recipes'


router = DefaultRouter()
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('users', CustomUsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

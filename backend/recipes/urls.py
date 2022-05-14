from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUsersViewSet, IngredientsViewSet, RecipesViewSet,
                    TagsViewSet)

app_name = 'recipes'


router = DefaultRouter()
router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'users', CustomUsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

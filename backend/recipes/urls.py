from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (RecipesViewSet, TagsViewSet,
                    IngredientsViewSet, CustomUsersViewSet)

app_name = 'recipes'


router = DefaultRouter()
router.register(r'recipes', RecipesViewSet)
router.register(r'tags', TagsViewSet)
router.register(r'ingredients', IngredientsViewSet)
router.register(r'users', CustomUsersViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

from .permissions import IsAdminOrReadOnly


class PermissionAndPaginationMixin:
    """
    Миксинкласс для вьюсетов ингредиентов и тегов
    """

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IsSubscribedMixin:
    """
    Миксинкласс для сериализаторов с полем подписки
    """

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        if not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()

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
        return (user.is_authenticated
                and user.follower.filter(author=obj).exists()
                )

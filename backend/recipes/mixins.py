from .permissions import IsAdminOrReadOnly
from rest_framework.pagination import LimitOffsetPagination


class PermissionAndPaginationMixin:
    """
    Миксинкласс:
    Разрешения = админ или только чтение;
    Пагинация = по указанию 'limit' или по-умолчанию.
    """

    permission_classes = (IsAdminOrReadOnly,)

    def get_pagination_class(self, data):
        limit = self.request.query_params.get('limit')
        if limit is None:
            return None
        return LimitOffsetPagination()

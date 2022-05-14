from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and not request.user.is_blocked)
        )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and not request.user.is_blocked)
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and not request.user.is_blocked
                and (
                    obj.author == request.user
                    or request.user.is_superuser
                )
            )
        )


class IsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and not request.user.is_blocked
        )

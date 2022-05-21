from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'username',
        'email',
        'first_name',
        'last_name',
        'is_blocked',
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_blocked', 'email', 'first_name')
    empty_value_display = '-пусто-'

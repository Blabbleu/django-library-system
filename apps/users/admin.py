"""
Admin module for the users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _
from django.contrib.auth.models import Group
from .models import CustomUser, Reader
from .forms import ReaderAdminForm

class UserAdmin(BaseUserAdmin):
    """Admin configuration for CustomUser model."""
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'date_of_birth',
                'address', 'phone_number', 'profile_picture'
            )
        }),
        (_('Professional info'), {
            'fields': ('level_of_education', 'department', 'position')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff',
        'department', 'position'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

class ReaderAdmin(admin.ModelAdmin):
    """Admin configuration for Reader model."""
    form = ReaderAdminForm
    list_display = (
        'user', 'date_of_birth', 'address', 'date_of_card_creation',
        'reader_type', 'owed_money', 'credit_score'
    )
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name', 'user__email'
    )
    ordering = ('user__username',)

# Unregister the default Group admin if you don't want to show it
admin.site.unregister(Group)

# Register the custom user admin
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Reader, ReaderAdmin)

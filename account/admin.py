from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomUser, Organization

@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = ('email', 'role', 'organization', 'is_active')
    list_filter = ('role', 'organization', 'is_active')
    search_fields = ('email', 'organization__name')
    ordering = ('email',)

@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)

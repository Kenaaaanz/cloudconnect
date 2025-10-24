# accounts/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import CustomUser, UserSession, LoginHistory

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'company_account_number', 'account_type', 'is_staff', 'date_joined')
    list_filter = ('account_type', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'company_account_number', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_updated')
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'company_account_number')
        }),
        ('Contact Info', {
            'fields': ('phone', 'address', 'city', 'state', 'country', 'zip_code')
        }),
        ('Account Info', {
            'fields': ('account_type', 'is_active', 'email_verified')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'last_updated')
        }),
    )

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'device_type', 'last_activity', 'is_active')
    list_filter = ('device_type', 'is_active', 'last_activity')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    readonly_fields = ('last_activity',)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'timestamp', 'success', 'reason')
    list_filter = ('success', 'timestamp')
    search_fields = ('user__username', 'ip_address', 'reason')
    readonly_fields = ('timestamp',)


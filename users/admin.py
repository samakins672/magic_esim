from django.contrib import admin
from .models import User, AccountDeletionLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "id")


@admin.register(AccountDeletionLog)
class AccountDeletionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "user_pk", "ip_address", "deleted_at", "method")
    search_fields = ("email", "user_pk", "ip_address")
    list_filter = ("method", "deleted_at")

from django.contrib import admin
from .models import User, FriendRequest

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'name', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['id']

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['sender__email', 'receiver__email']
    ordering = ['created_at']

from django.contrib import admin
from .models import UserProfile, Service, HelpRequest, Message, Review, Request, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'phone']
    search_fields = ['user__username', 'skills_offered', 'location']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'payment_type', 'location', 'created_at']
    list_filter = ['category', 'payment_type']
    search_fields = ['title', 'description', 'user__username', 'location']

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['service', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['service__title', 'sender__username', 'receiver__username', 'message']

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description', 'user__username']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'service', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['message', 'sender__username', 'receiver__username']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['service', 'author', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'author__username', 'service__title']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'notif_type', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read', 'created_at']
    search_fields = ['message', 'user__username']

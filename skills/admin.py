from django.contrib import admin
from .models import UserProfile, ServicePost, ServiceRequest, Message, Review

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'phone']
    search_fields = ['user__username', 'skills_offered', 'location']

@admin.register(ServicePost)
class ServicePostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'price_type', 'location', 'created_at']
    list_filter = ['category', 'price_type']
    search_fields = ['title', 'description', 'author__username', 'location']

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'requester', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description', 'requester__username']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['content', 'sender__username', 'recipient__username']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['service', 'author', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'author__username', 'service__title']

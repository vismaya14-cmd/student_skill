from django.contrib import admin
from .models import UserProfile, ServicePost, ServiceRequest, Message, Review, ServiceBooking

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'phone']
    search_fields = ['user__username', 'skills_offered', 'location']

@admin.register(ServicePost)
class ServicePostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'payment_type', 'location', 'created_at']
    list_filter = ['category', 'payment_type']
    search_fields = ['title', 'description', 'author__username', 'location']

@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ['service', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['service__title', 'sender__username', 'receiver__username', 'message']

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'requester', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description', 'requester__username']

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

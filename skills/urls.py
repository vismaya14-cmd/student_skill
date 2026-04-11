from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('requests/', views.requests_hub, name='requests_hub'),
    path('search/', views.search, name='search'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_messages, name='sent_messages'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('post-service/', views.post_service, name='post_service'),
    path('post-request/', views.post_request, name='post_request'),
    path('service/<int:pk>/', views.service_detail, name='service_detail'),
    path('booking-inbox/', views.booking_inbox, name='booking_inbox'),
    path('manage-booking/<int:pk>/<str:action>/', views.manage_booking, name='manage_booking'),
    path('request/accept/<int:id>/', views.accept_request, name='accept_request'),
    path('request/reject/<int:id>/', views.reject_request, name='reject_request'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-service/<int:pk>/', views.delete_service, name='delete_service'),
    path('payment/<int:service_id>/', views.payment_view, name='payment'),
    path('payment-success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('register/', views.register, name='register'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('requests/', views.requests_hub, name='requests_hub'),
    path('search/', views.search, name='search'),
    path('inbox/', views.inbox, name='inbox'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('post-service/', views.post_service, name='post_service'),
    path('post-request/', views.post_request, name='post_request'),
    path('service/<int:pk>/', views.service_detail, name='service_detail'),
    path('my-services/', views.my_services, name='my_services'),
    path('delete-service/<int:pk>/', views.delete_service, name='delete_service'),
    path('register/', views.register, name='register'),
]

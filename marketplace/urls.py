from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('skills.urls')),
    path('polls/', RedirectView.as_view(url='/', permanent=True)),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Override accounts/login/ and accounts/logout/ to use custom templates
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='accounts_login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='accounts_logout'),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

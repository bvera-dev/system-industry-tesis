from django.contrib import admin
from django.urls import path, include
from core_apps.common.views import IndexView, DashboardView, register_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login2.html'), name='login'),
    path('', IndexView.as_view(), name='home'),  # Página protegida con LoginRequiredMixin
    path('register/', register_view, name='register'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('camera/', include('core_apps.camera.urls')),
    path('informes/', include('core_apps.informes.urls')),
    path('admin/', admin.site.urls),

    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]


from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from core_apps.common.views import DashboardView, IndexView, register_view

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login2.html"), name="login"),
    path("", IndexView.as_view(), name="home"),
    path("register/", register_view, name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("camera/", include("core_apps.camera.urls")),
    path("informes/", include("core_apps.informes.urls")),
    path("admin/", admin.site.urls),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
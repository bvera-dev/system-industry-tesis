from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_informes, name='lista_informes'),
]

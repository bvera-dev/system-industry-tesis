from django.views.generic import TemplateView

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

# Create your views here.
#  Vista basada en clases  
class IndexView(LoginRequiredMixin,TemplateView):
    template_name = 'home.html'
    login_url = '/login/'  # Redirige si no está autenticado

class DashboardView(TemplateView):
    template_name = 'includes/dashboard.html'


#modificacion
#def login_view(request):
#   if request.method == 'POST':
#        username = request.POST.get('username')
#        password = request.POST.get('password')
#
#        user = authenticate(request, username=username, password=password)
#
#        if user is not None:
#            login(request, user)
#            return redirect('home')  # Asegúrate que esta URL exista
#        else:
#            messages.error(request, 'Usuario o contraseña incorrectos')
#
#       return render(request, 'accounts/login.html') 


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # redirige al login luego del registro
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})
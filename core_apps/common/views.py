from django.views.generic import TemplateView
from django import forms
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta

from core_apps.camera.models import SecurityEvent, AuthorizedPerson
from core_apps.informes.models import Informe

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def settings_view(request):
    return render(request, "home/settings.html")

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'home/index.html'
    login_url = '/login/'

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {
        "form": form
    })


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'home/dashboard.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        now = timezone.localtime()

        # =========================
        # Métricas principales
        # =========================
        total_events_today = SecurityEvent.objects.filter(
            timestamp__date=today
        ).count()

        critical_alerts = SecurityEvent.objects.filter(
            resolved=False,
            event_type__in=[
                'dangerous_object',
                'unauthorized_access',
                'face_unknown'
            ]
        ).count()

        informes_today = Informe.objects.filter(
            fecha__date=today
        ).count()

        total_reports = Informe.objects.count()
        epp_ok_count = Informe.objects.filter(epp_correcto=True).count()
        epp_incorrect_count = total_reports - epp_ok_count

        if total_reports > 0:
            epp_percent = round((epp_ok_count / total_reports) * 100)
            epp_incorrect_percent = 100 - epp_percent
        else:
            epp_percent = 0
            epp_incorrect_percent = 0

        authorized_people = AuthorizedPerson.objects.filter(
            is_active=True
        ).count()

        pending_events = SecurityEvent.objects.filter(
            resolved=False
        ).count()

        resolved_events = SecurityEvent.objects.filter(
            resolved=True
        ).count()

        total_events = SecurityEvent.objects.count()

        # =========================
        # Últimos registros
        # =========================
        recent_events = SecurityEvent.objects.select_related(
            'related_user'
        ).all()[:5]

        recent_reports = Informe.objects.order_by('-fecha')[:5]

        last_event = SecurityEvent.objects.first()

        # =========================
        # Eventos últimos 7 días
        # =========================
        start_day = today - timedelta(days=6)
        days = [start_day + timedelta(days=i) for i in range(7)]

        raw_weekly = (
            SecurityEvent.objects
            .filter(timestamp__date__gte=start_day, timestamp__date__lte=today)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(total=Count('id'))
        )

        weekly_map = {
            item['day']: item['total']
            for item in raw_weekly
        }

        weekly_labels = [
            day.strftime('%d/%m')
            for day in days
        ]

        weekly_values = [
            weekly_map.get(day, 0)
            for day in days
        ]

        # =========================
        # Distribución por tipo de evento
        # =========================
        event_type_display = dict(SecurityEvent.EVENT_TYPES)

        raw_distribution = (
            SecurityEvent.objects
            .values('event_type')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        event_breakdown = []

        for item in raw_distribution:
            event_type = item['event_type']

            event_breakdown.append({
                'key': event_type,
                'label': event_type_display.get(event_type, event_type),
                'total': item['total'],
            })

        event_labels = [
            item['label']
            for item in event_breakdown
        ]

        event_values = [
            item['total']
            for item in event_breakdown
        ]

        # Para evitar que el gráfico falle si aún no hay eventos
        if not event_labels:
            event_labels = ['Sin eventos']
            event_values = [1]

        context.update({
            'segment': 'dashboard',

            'today': today,
            'now': now,

            'total_events': total_events,
            'total_events_today': total_events_today,
            'critical_alerts': critical_alerts,
            'informes_today': informes_today,

            'epp_percent': epp_percent,
            'epp_incorrect_percent': epp_incorrect_percent,
            'epp_ok_count': epp_ok_count,
            'epp_incorrect_count': epp_incorrect_count,

            'authorized_people': authorized_people,
            'pending_events': pending_events,
            'resolved_events': resolved_events,

            'recent_events': recent_events,
            'recent_reports': recent_reports,
            'last_event': last_event,

            'weekly_labels': weekly_labels,
            'weekly_values': weekly_values,

            'event_labels': event_labels,
            'event_values': event_values,
            'event_breakdown': event_breakdown,
        })

        return context
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class AuthorizedPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    face_encoding = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    encoding = models.TextField(null=True, blank=True)  # evargas


    def __str__(self):
        return self.user.username

class SecurityEvent(models.Model):
    EVENT_TYPES = (
        ('face_recognized', 'Rostro reconocido'),
        ('face_unknown', 'Rostro desconocido'),
        ('dangerous_object', 'Objeto peligroso detectado'),
        ('unauthorized_access', 'Acceso no autorizado'),
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    details = models.TextField()
    image_path = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Evento de Seguridad'
        verbose_name_plural = 'Eventos de Seguridad'

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_image_url(self):
        if self.image_path:
            return settings.MEDIA_URL + self.image_path
        return None
from django.conf import settings
from datetime import datetime
from core_apps.camera.models import SecurityEvent
from core_apps.informes.models import Informe
import os

# OpenCV como import seguro
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None


def save_event_image(frame, event_type):
    """
    Guarda la imagen del evento y devuelve la ruta relativa.
    Ejemplo de retorno: security_events/unauthorized_access_20260408_154500_123456.jpg
    """
    try:
        if cv2 is None or frame is None:
            return None

        # Crear directorio si no existe
        events_dir = os.path.join(settings.MEDIA_ROOT, 'security_events')
        os.makedirs(events_dir, exist_ok=True)

        # Nombre único con microsegundos para evitar duplicados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{event_type}_{timestamp}.jpg"

        filepath = os.path.join('security_events', filename).replace("\\", "/")
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)

        # Guardar imagen
        saved = cv2.imwrite(full_path, frame)

        if saved:
            return filepath

        return None

    except Exception as e:
        print(f"Error al guardar imagen de evento: {e}")
        return None


def create_security_event(event_type, details, frame=None, user=None, camara="Cámara 1", epp_correcto=None):
    """
    Crea un evento de seguridad y su informe correspondiente.
    """

    try:
        # 1. Guardar imagen si existe frame
        image_path = save_event_image(frame, event_type)

        # 2. Crear evento de seguridad
        event = SecurityEvent.objects.create(
            event_type=event_type,
            details=details,
            image_path=image_path,
            related_user=user
        )

        # 3. Nombre de persona
        if user:
            persona = user.get_full_name().strip() or user.username
        else:
            persona = "Desconocido"

        # 4. Determinar EPP correcto
        # Si no lo mandan, por defecto queda en False
        if epp_correcto is None:
            epp_correcto = False

        # 5. Crear informe
        Informe.objects.create(
            camara=camara,
            persona_detectada=persona,
            epp_correcto=epp_correcto,
            descripcion=f"{event.get_event_type_display()}: {details}"
        )

        return event

    except Exception as e:
        print(f"[ERROR] No se pudo crear evento/informe: {e}")
        return None
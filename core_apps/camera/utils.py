from django.conf import settings
from datetime import datetime
from core_apps.camera.models import SecurityEvent
from core_apps.informes.models import Informe

import os

# OpenCV y NumPy son dependencias pesadas. Para que el proyecto pueda
# arrancar aunque no estén instaladas (por ejemplo, si solo quieres usar
# el módulo de informes), hacemos la importación de forma segura.
try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

def save_event_image(frame, event_type):
    """Guarda la imagen del evento y devuelve la ruta relativa"""
    try:
        if cv2 is None or frame is None:
            return None

        # Crear directorio si no existe
        events_dir = os.path.join(settings.MEDIA_ROOT, 'security_events')
        os.makedirs(events_dir, exist_ok=True)
        
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{event_type}_{timestamp}.jpg"
        filepath = os.path.join('security_events', filename)
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)
        
        # Guardar imagen
        cv2.imwrite(full_path, frame)
        
        return filepath
    except Exception as e:
        print(f"Error al guardar imagen de evento: {e}")
        return None
        

def create_security_event(event_type, details, frame=None, user=None):
    """
    Crea un evento de seguridad y registra informe correspondiente
    """
    try:
        from core_apps.informes.models import Informe

        # 1. Guardar imagen del evento (opcional)
        image_path = save_event_image(frame, event_type)

        # 2. Crear evento de seguridad
        event = SecurityEvent.objects.create(
            event_type=event_type,
            details=details,
            image_path=image_path,
            related_user=user
        )

        # 3. Lógica del informe
        persona = user.username if user else "Desconocido"
        epp_correcto = False

        if event_type in ['face_recognized']:
            epp_correcto = True  # Puedes refinarlo según detección real de EPP

        # Siempre guardar en informe
        Informe.objects.create(
            camara="Cámara 1",
            persona_detectada=persona,
            epp_correcto=epp_correcto,
            descripcion=f"{event.get_event_type_display()}: {details}"
        )

        return event

    except Exception as e:
        print(f"[ERROR] No se pudo crear evento/informe: {e}")
        return None

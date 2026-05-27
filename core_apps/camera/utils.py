from datetime import datetime
import uuid

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from core_apps.camera.models import SecurityEvent
from core_apps.informes.models import Informe

# OpenCV como import seguro
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None


def build_event_image_path(event_type):
    """
    Construye una ruta organizada para guardar evidencias.

    Ejemplo:
    security_events/2026/05/25/dangerous_object_20260525_224510_a1b2c3d4.jpg
    """

    now = timezone.localtime()
    unique_id = uuid.uuid4().hex[:8]

    filename = f"{event_type}_{now.strftime('%Y%m%d_%H%M%S')}_{unique_id}.jpg"

    return (
        f"security_events/"
        f"{now.year}/"
        f"{now.month:02d}/"
        f"{now.day:02d}/"
        f"{filename}"
    )


def save_event_image(frame, event_type, jpeg_quality=85):
    """
    Guarda la imagen del evento y devuelve la ruta relativa.

    En local guarda en:
    media/security_events/año/mes/día/imagen.jpg

    En base de datos guarda solo:
    security_events/año/mes/día/imagen.jpg
    """

    try:
        if cv2 is None:
            print("[ERROR] OpenCV no está instalado.")
            return None

        if frame is None:
            print("[ERROR] No se recibió frame para guardar evidencia.")
            return None

        image_path = build_event_image_path(event_type)

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        )

        if not success:
            print("[ERROR] No se pudo convertir el frame a JPG.")
            return None

        image_file = ContentFile(buffer.tobytes())

        saved_path = default_storage.save(image_path, image_file)

        return saved_path

    except Exception as e:
        print(f"[ERROR] Error al guardar imagen de evento: {e}")
        return None


def can_save_event(event_key, seconds=20):
    """
    Evita guardar muchas evidencias repetidas del mismo evento.

    Ejemplo:
    Si detecta un objeto peligroso durante varios segundos,
    solo guardará una evidencia cada 20 segundos.
    """

    if cache.get(event_key):
        return False

    cache.set(event_key, True, timeout=seconds)
    return True


def create_security_event(
    event_type,
    details,
    frame=None,
    user=None,
    camara="Cámara 1",
    epp_correcto=None
):
    """
    Crea un evento de seguridad, guarda su evidencia y crea su informe.
    """

    try:
        # 1. Guardar imagen si existe frame
        image_path = None

        if frame is not None:
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
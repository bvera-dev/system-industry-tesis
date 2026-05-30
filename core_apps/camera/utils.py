import os
from datetime import datetime

from django.conf import settings

from core_apps.camera.models import SecurityEvent
from core_apps.informes.models import Informe

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None


EPP_EVENT_TYPES = {"ppe_missing", "ppe_incorrect"}


def save_event_image(frame, event_type):
    """
    Guarda la imagen del evento y devuelve la ruta relativa.
    Ejemplo de retorno:
    security_events/ppe_missing_20260503_154500_123456.jpg
    """
    try:
        if cv2 is None or frame is None:
            return None

        events_dir = os.path.join(settings.MEDIA_ROOT, "security_events")
        os.makedirs(events_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{event_type}_{timestamp}.jpg"
        filepath = os.path.join("security_events", filename).replace("\\", "/")
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)

        saved = cv2.imwrite(full_path, frame)
        if saved:
            return filepath
        return None

    except Exception as e:
        print(f"Error al guardar imagen de evento: {e}")
        return None


def _resolve_person_name(user):
    if user:
        full_name = user.get_full_name().strip()
        return full_name if full_name else user.username
    return "Desconocido"


def _should_create_report(event_type: str) -> bool:
    return event_type in EPP_EVENT_TYPES


def _resolve_epp_correcto(event_type: str, epp_correcto):
    if epp_correcto is not None:
        return epp_correcto

    if event_type in EPP_EVENT_TYPES:
        return False

    return None


def create_security_event(
    event_type,
    details,
    frame=None,
    user=None,
    camara="Cámara 1",
    epp_correcto=None,
):
    """
    Crea un evento de seguridad y, solo si corresponde,
    genera un informe asociado.
    """
    try:
        image_path = save_event_image(frame, event_type)

        event = SecurityEvent.objects.create(
            event_type=event_type,
            details=details,
            image_path=image_path,
            related_user=user,
        )

        if _should_create_report(event_type):
            persona = _resolve_person_name(user)
            epp_value = _resolve_epp_correcto(event_type, epp_correcto)

            Informe.objects.create(
                camara=camara,
                persona_detectada=persona,
                epp_correcto=epp_value if epp_value is not None else False,
                descripcion=f"{event.get_event_type_display()}: {details}",
            )

        return event

    except Exception as e:
        print(f"[ERROR] No se pudo crear evento/informe: {e}")
        return None
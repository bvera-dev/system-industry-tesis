from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators import gzip
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .models import AuthorizedPerson, SecurityEvent
from .services.camera_provider import open_camera_stream, probe_camera
from .services.frame_analyzer import gen_frames
from .services.live_log import get_live_log, log_line
from .services.model_loader import safe_import_face_recognition


@require_GET
@login_required
def live_status(request):
    try:
        after = int(request.GET.get("after", "0"))
    except ValueError:
        after = 0

    return JsonResponse(get_live_log(after=after, limit=80))


@require_GET
@login_required
def camera_status(request):
    cap, error = probe_camera()

    if error:
        log_line(f"❌ {error}", key="cam_status_fail", throttle_sec=5)
        return JsonResponse(
            {"success": False, "message": error},
            status=400,
        )

    cap.release()
    return JsonResponse(
        {"success": True, "message": "Cámara disponible"},
        status=200,
    )


@require_GET
@login_required
@gzip.gzip_page
def video_feed(request):
    try:
        fps = int(request.GET.get("fps", "12"))
    except ValueError:
        fps = 8

    stream, error = open_camera_stream()
    if error:
        log_line(f"❌ {error}", key="cam_fail_stream", throttle_sec=5)
        return JsonResponse(
            {"success": False, "message": error},
            status=400,
        )

    return StreamingHttpResponse(
        gen_frames(stream=stream, target_fps=fps),
        content_type="multipart/x-mixed-replace;boundary=frame",
    )


@require_POST
@login_required
def register_face(request):
    face_recognition = safe_import_face_recognition()
    if face_recognition is None:
        return JsonResponse(
            {"success": False, "message": "face_recognition no está instalado"},
            status=400,
        )

    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"success": False, "message": "No image uploaded"}, status=400)

    image_data = face_recognition.load_image_file(image_file)
    face_locations = face_recognition.face_locations(image_data)
    if not face_locations:
        return JsonResponse({"success": False, "message": "No face detected"}, status=400)

    encodings = face_recognition.face_encodings(image_data, face_locations)
    if not encodings:
        return JsonResponse({"success": False, "message": "No encoding found"}, status=400)

    encoding_json = json.dumps(encodings[0].tolist())
    person, _created = AuthorizedPerson.objects.get_or_create(user=request.user)
    person.face_encoding = encoding_json
    person.encoding = encoding_json
    person.is_active = True
    person.save()

    log_line(f"✅ Rostro registrado para: {request.user.username}", key="face_registered", throttle_sec=1.5)
    return JsonResponse({"success": True, "message": "Face registered successfully"})


@require_GET
@login_required
def get_events(request):
    events = SecurityEvent.objects.order_by("-timestamp")[:50]
    data = [
        {
            "id": event.id,
            "event_type": event.event_type,
            "event_type_display": event.get_event_type_display(),
            "details": event.details,
            "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved": event.resolved,
            "image_url": event.get_image_url() if hasattr(event, "get_image_url") else None,
        }
        for event in events
    ]
    return JsonResponse({"events": data})


@require_GET
@login_required
def get_security_events(request):
    events = SecurityEvent.objects.all().order_by("-timestamp")[:50]
    events_data = []
    for event in events:
        events_data.append(
            {
                "id": event.id,
                "event_type": event.event_type,
                "event_type_display": event.get_event_type_display(),
                "details": event.details,
                "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved": event.resolved,
                "image_url": event.get_image_url() if hasattr(event, "get_image_url") else None,
                "user": event.related_user.username if getattr(event, "related_user", None) else "Sistema",
            }
        )
    return JsonResponse({"events": events_data})


@require_POST
@login_required
def mark_event_resolved(request, event_id):
    event = get_object_or_404(SecurityEvent, id=event_id)
    event.resolved = True
    event.save()
    log_line(f"✅ Evento resuelto: {event_id}", key=f"ev_res_{event_id}", throttle_sec=0.5)
    return JsonResponse({"status": "success"})


class CameraView(LoginRequiredMixin, TemplateView):
    template_name = "camera/camera.html"


class AlertaView(LoginRequiredMixin, TemplateView):
    template_name = "camera/alerta.html"
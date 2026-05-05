from __future__ import annotations

import time
from collections import deque
from threading import Lock

_LIVE_LOG = deque(maxlen=300)
_LOG_LOCK = Lock()
_LOG_SEQ = 0
_LAST_LOG_TS: dict[str, float] = {}


def log_line(message: str, key: str | None = None, throttle_sec: float = 0.0) -> None:
    global _LOG_SEQ
    now = time.monotonic()

    if key and throttle_sec > 0:
        last = _LAST_LOG_TS.get(key, 0.0)
        if (now - last) < throttle_sec:
            return
        _LAST_LOG_TS[key] = now

    ts = time.strftime("%H:%M:%S")

    with _LOG_LOCK:
        _LOG_SEQ += 1
        _LIVE_LOG.append({"id": _LOG_SEQ, "ts": ts, "msg": message})


def get_live_log(after: int = 0, limit: int = 80) -> dict:
    with _LOG_LOCK:
        last_id = _LOG_SEQ
        lines = [x for x in _LIVE_LOG if x["id"] > after]
        lines = lines[-limit:]

    return {"lines": lines, "last_id": last_id}
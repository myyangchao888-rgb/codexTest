from typing import Dict, Any, List
import threading

_zones: Dict[int, Dict[str, Any]] = {}
_zone_status: Dict[int, Dict[str, Any]] = {}
_events: List[Dict[str, Any]] = []
_zone_schema: List[str] = []
_zone_status_schema: List[str] = []
_host_info: Dict[str, Any] = {}
_lock = threading.Lock()


def upsert_zone(rec: Dict[str, Any]) -> None:
    with _lock:
        _zones[rec["id"]] = rec


def upsert_zone_status(rec: Dict[str, Any]) -> None:
    with _lock:
        _zone_status[rec["id"]] = rec


def set_zone_schema(schema: List[str]) -> None:
    with _lock:
        _zone_schema[:] = schema


def set_zone_status_schema(schema: List[str]) -> None:
    with _lock:
        _zone_status_schema[:] = schema


def set_host_info(key: str, value: Any) -> None:
    with _lock:
        _host_info[key] = value


def set_zone_arm(zone_id: int, arm: int) -> None:
    """Update the arm state for a single zone."""
    with _lock:
        rec = _zone_status.get(zone_id)
        if rec:
            rec["arm"] = arm
        else:
            _zone_status[zone_id] = {
                "id": zone_id,
                "arm": arm,
                "bypass": 0,
                "sta": "",
                "acnt": 0,
            }


def add_event(evt: Dict[str, Any], raw: str) -> None:
    event = {
        "ts": evt.get("ts"),
        "type": evt.get("type"),
        "params": evt.get("params", []),
        "raw": raw,
    }
    with _lock:
        _events.append(event)


def fetch_zones() -> List[Dict[str, Any]]:
    with _lock:
        return sorted(_zones.values(), key=lambda r: r["id"])


def fetch_zone_status() -> List[Dict[str, Any]]:
    with _lock:
        return sorted(_zone_status.values(), key=lambda r: r["id"])


def fetch_events(limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        return list(_events[-limit:])[::-1]


def fetch_host_info() -> Dict[str, Any]:
    with _lock:
        return dict(_host_info)


def fetch_zone_schema() -> List[str]:
    with _lock:
        return list(_zone_schema)


def fetch_zone_status_schema() -> List[str]:
    with _lock:
        return list(_zone_status_schema)

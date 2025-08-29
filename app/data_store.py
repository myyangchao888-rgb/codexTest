from typing import Dict, Any, List
import threading

# host_id -> host data structure
_hosts: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def _get_host(host_id: str) -> Dict[str, Any]:
    """Return the host record for *host_id*, creating it if necessary."""
    host = _hosts.get(host_id)
    if not host:
        host = {
            "info": {"id": host_id},
            "zones": {},
            "zone_status": {},
            "events": [],
            "zone_schema": [],
            "zone_status_schema": [],
        }
        _hosts[host_id] = host
    return host


def upsert_zone(host_id: str, rec: Dict[str, Any]) -> None:
    with _lock:
        _get_host(host_id)["zones"][rec["id"]] = rec


def upsert_zone_status(host_id: str, rec: Dict[str, Any]) -> None:
    with _lock:
        _get_host(host_id)["zone_status"][rec["id"]] = rec


def set_zone_schema(host_id: str, schema: List[str]) -> None:
    with _lock:
        _get_host(host_id)["zone_schema"] = list(schema)


def set_zone_status_schema(host_id: str, schema: List[str]) -> None:
    with _lock:
        _get_host(host_id)["zone_status_schema"] = list(schema)


def set_host_info(host_id: str, key: str, value: Any) -> None:
    with _lock:
        _get_host(host_id)["info"][key] = value


def set_zone_arm(host_id: str, zone_id: int, arm: int) -> None:
    """Update the arm state for a single zone."""
    with _lock:
        host = _get_host(host_id)
        rec = host["zone_status"].get(zone_id)
        if rec:
            rec["arm"] = arm
        else:
            host["zone_status"][zone_id] = {
                "id": zone_id,
                "arm": arm,
                "bypass": 0,
                "sta": "",
                "acnt": 0,
            }


def add_event(host_id: str, evt: Dict[str, Any], raw: str) -> None:
    event = {
        "ts": evt.get("ts"),
        "type": evt.get("type"),
        "type_desc": evt.get("type_desc", evt.get("type")),
        "params": evt.get("params", {}),
        "raw": raw,
    }
    with _lock:
        _get_host(host_id)["events"].append(event)


def fetch_hosts() -> List[Dict[str, Any]]:
    """Return host info records for all known hosts."""
    with _lock:
        return [dict(h["info"]) for h in _hosts.values()]


def fetch_zones(host_id: str) -> List[Dict[str, Any]]:
    with _lock:
        host = _hosts.get(host_id)
        if not host:
            return []
        return sorted(host["zones"].values(), key=lambda r: r["id"])


def fetch_zone_status(host_id: str) -> List[Dict[str, Any]]:
    with _lock:
        host = _hosts.get(host_id)
        if not host:
            return []
        return sorted(host["zone_status"].values(), key=lambda r: r["id"])


def fetch_events(host_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    with _lock:
        host = _hosts.get(host_id)
        if not host:
            return []
        return list(host["events"][-limit:])[::-1]


def fetch_host_info(host_id: str) -> Dict[str, Any]:
    with _lock:
        host = _hosts.get(host_id)
        return dict(host["info"]) if host else {}


def fetch_zone_schema(host_id: str) -> List[str]:
    with _lock:
        host = _hosts.get(host_id)
        return list(host["zone_schema"]) if host else []


def fetch_zone_status_schema(host_id: str) -> List[str]:
    with _lock:
        host = _hosts.get(host_id)
        return list(host["zone_status_schema"]) if host else []

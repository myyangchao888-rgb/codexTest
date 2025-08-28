from fastapi import FastAPI, Query, HTTPException
from typing import List
from . import data_store
from .tcp_server import (
    connected_hosts,
    arm_zone,
    disarm_zone,
    arm_host,
    disarm_host,
    log_http_data,
    last_report_time,
)

app = FastAPI(title="Alarm Host API", version="1.0.0")


@app.get("/devices", response_model=List[dict])
def list_devices():
    hosts = []
    for host_id in connected_hosts():
        info = data_store.fetch_host_info(host_id)
        info.setdefault("id", host_id)
        hosts.append(info)
    return hosts


@app.get("/devices/{host_id}/zones")
def get_zones(host_id: str):
    zones = data_store.fetch_zones(host_id)
    if not zones:
        log_http_data(host_id)
    return zones


@app.get("/devices/{host_id}/zone-status")
def get_zone_status(host_id: str):
    status = data_store.fetch_zone_status(host_id)
    if not status:
        log_http_data(host_id)
    return status


@app.get("/devices/{host_id}/events")
def get_events(host_id: str, limit: int = Query(50, ge=1, le=1000)):
    events = data_store.fetch_events(host_id, limit=limit)
    if not events:
        log_http_data(host_id)
    return events


@app.get("/devices/{host_id}/info")
def host_info(host_id: str):
    info = data_store.fetch_host_info(host_id)
    if not info:
        log_http_data(host_id)
    return info


@app.post("/devices/{host_id}/zones/{zone_id}/arm")
def http_arm_zone(host_id: str, zone_id: int):
    if not arm_zone(host_id, zone_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"zone_id": zone_id, "armed": True}


@app.post("/devices/{host_id}/zones/{zone_id}/disarm")
def http_disarm_zone(host_id: str, zone_id: int):
    if not disarm_zone(host_id, zone_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"zone_id": zone_id, "armed": False}


@app.post("/devices/{host_id}/arm")
def http_arm_host(host_id: str):
    if not arm_host(host_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"armed": True}


@app.post("/devices/{host_id}/disarm")
def http_disarm_host(host_id: str):
    if not disarm_host(host_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"armed": False}


@app.get("/devices/{host_id}/health")
def health(host_id: str):
    import time
    last_ts = last_report_time(host_id)
    return {
        "alive": True,
        "last_report_unix": last_ts,
        "last_report_ago_sec": (time.time() - last_ts) if last_ts > 0 else None,
    }

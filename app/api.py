from fastapi import FastAPI, Query, HTTPException
from . import data_store
from .tcp_server import (
    last_report_time,
    arm_zone,
    disarm_zone,
    arm_host,
    disarm_host,
    log_http_data,
)

app = FastAPI(title="Alarm Host API", version="1.0.0")

@app.get("/zones")
def get_zones():
    zones = data_store.fetch_zones()
    if not zones:
        log_http_data()
    return zones

@app.get("/zone-status")
def get_zone_status():
    status = data_store.fetch_zone_status()
    if not status:
        log_http_data()
    return status

@app.get("/events")
def get_events(limit: int = Query(50, ge=1, le=1000)):
    events = data_store.fetch_events(limit=limit)
    if not events:
        log_http_data()
    return events


@app.get("/host/info")
def host_info():
    info = data_store.fetch_host_info()
    if not info:
        log_http_data()
    return info


@app.post("/zones/{zone_id}/arm")
def http_arm_zone(zone_id: int):
    if not arm_zone(zone_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"zone_id": zone_id, "armed": True}


@app.post("/zones/{zone_id}/disarm")
def http_disarm_zone(zone_id: int):
    if not disarm_zone(zone_id):
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"zone_id": zone_id, "armed": False}


@app.post("/host/arm")
def http_arm_host():
    if not arm_host():
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"armed": True}


@app.post("/host/disarm")
def http_disarm_host():
    if not disarm_host():
        raise HTTPException(status_code=503, detail="alarm host not connected")
    return {"armed": False}

@app.get("/host/health")
def health():
    import time
    last_ts = last_report_time()
    return {
        "alive": True,
        "last_report_unix": last_ts,
        "last_report_ago_sec": (time.time() - last_ts) if last_ts > 0 else None
    }

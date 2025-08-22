from fastapi import FastAPI, Query
from . import db
from .tcp_server import last_report_time

app = FastAPI(title="Alarm Host API", version="1.0.0")

@app.get("/zones")
def get_zones():
    return db.fetch_zones()

@app.get("/zone-status")
def get_zone_status():
    return db.fetch_zone_status()

@app.get("/events")
def get_events(limit: int = Query(50, ge=1, le=1000)):
    return db.fetch_events(limit=limit)

@app.get("/host/health")
def health():
    import time
    last_ts = last_report_time()
    return {
        "alive": True,
        "last_report_unix": last_ts,
        "last_report_ago_sec": (time.time() - last_ts) if last_ts > 0 else None
    }

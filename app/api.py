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

IO_DESC = {"I": "输入型防区", "O": "输出型防区"}
ENA_DESC = {1: "正常", 0: "禁止"}
TYPE_DESC = {
    "NORMAL": "普通",
    "DELAY": "延时",
    "A24H": "有声24小时",
    "S24H": "无声24小时",
    "INSIDE": "内部",
    "PERM": "周界",
    "EMERG": "紧急",
    "FIRE": "火警",
    "GAS": "燃气",
    "MEDICAL": "医疗",
    "BA24H": "24小时盗警",
    "DOORBELL": "门铃",
    "TAMPER": "防拆",
    "REMOTER": "遥控器",
    "KEYPAD": "键盘按钮",
}
ARM_DESC = {1: "布防", 0: "撤防"}
BYPASS_DESC = {1: "旁路", 0: "正常"}
STA_DESC = {
    "READY": "防区正常状态",
    "TRIG": "防区触发状态",
    "ALARM": "防区报警状态",
}

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
    else:
        for z in zones:
            z["io_desc"] = IO_DESC.get(z.get("io"), z.get("io"))
            z["ena_desc"] = ENA_DESC.get(z.get("ena"), str(z.get("ena")))
            z["type_desc"] = TYPE_DESC.get(z.get("type"), z.get("type"))
    return zones


@app.get("/devices/{host_id}/zone-status")
def get_zone_status(host_id: str):
    status = data_store.fetch_zone_status(host_id)
    if not status:
        log_http_data(host_id)
    else:
        for s in status:
            s["arm_desc"] = ARM_DESC.get(s.get("arm"), str(s.get("arm")))
            s["bypass_desc"] = BYPASS_DESC.get(s.get("bypass"), str(s.get("bypass")))
            s["sta_desc"] = STA_DESC.get(s.get("sta"), s.get("sta"))
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

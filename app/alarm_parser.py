from typing import Dict, Any, List, Optional


# Mapping of CWMSG event types to parameter names and Chinese descriptions
CWMSG_DEFS: Dict[str, Dict[str, Any]] = {
    "DFA_ALARM": {"desc": "防区报警", "params": ["zone", "code"]},
    "DFA_RESTORE": {"desc": "防区报警恢复", "params": ["zone", "code"]},
    "USER_SETARM": {"desc": "用户布防", "params": ["p1", "p2", "p3", "p4", "p5"]},
    "USER_DISARM": {"desc": "用户撤防", "params": ["p1", "p2", "p3", "p4", "p5"]},
    "DEV_ONLINE": {"desc": "子设备在线", "params": ["dev"]},
    "DEV_OFFLINE": {"desc": "子设备掉线", "params": ["dev"]},
    "DFA_BYPASS": {"desc": "防区旁路", "params": ["dev", "zone", "user"]},
    "DFA_FORCE": {"desc": "防区异常", "params": ["dev", "zone", "user"]},
    "POWERON": {"desc": "设备启动", "params": []},
    "STAT_AC": {"desc": "交流供电状态", "params": ["state", "source", "voltage"]},
    "STAT_BAT": {"desc": "电池状态", "params": ["status", "voltage"]},
    "STAT_PSTN": {"desc": "电话线状态", "params": ["status"]},
    "USER_LOGIN": {"desc": "用户登陆", "params": ["login", "dev", "user"]},
    "SETTM": {"desc": "配置修改", "params": []},
    "ZONE_TAMPER": {"desc": "防区拆动", "params": ["zone", "trig"]},
    "ZONE_LOWBAT": {"desc": "电池低压", "params": ["zone", "low"]},
    "ZONE_ACLOSS": {"desc": "防区断电", "params": ["zone", "loss"]},
    "ZONE_FAULT": {"desc": "防区故障", "params": ["zone", "fault"]},
    "SYS_RESTART": {"desc": "报警主机重启", "params": []},
    "SYS_HALT": {"desc": "报警主机关闭", "params": []},
    "SYS_TAMPER": {"desc": "报警主机拆动", "params": []},
    "COMMON": {"desc": "未定义消息", "params": ["p1", "p2"]},
}

def _split_csv(payload: str) -> List[str]:
    return [p.strip() for p in payload.split(",")]

def parse_dfai_line(line: str) -> Optional[Dict[str, Any]]:
    if not line.startswith("+DFAI"):
        return None
    payload = line.split(":", 1)[1].strip()
    fields = _split_csv(payload)
    if fields and fields[0].lower() == "id":
        return {"_schema": fields}
    try:
        return {
            "id": int(fields[0]),
            "io": fields[1],
            "ena": int(fields[2]),
            "type": fields[3],
            "code": int(fields[4]),
            "team": int(fields[5]),
            "name": fields[6] if len(fields) > 6 else ""
        }
    except Exception:
        return None

def parse_dfas_line(line: str) -> Optional[Dict[str, Any]]:
    if not line.startswith("+DFAS"):
        return None
    payload = line.split(":", 1)[1].strip()
    fields = _split_csv(payload)
    if fields and fields[0].lower() == "id":
        return {"_schema": fields}
    try:
        return {
            "id": int(fields[0]),
            "arm": int(fields[1]),
            "bypass": int(fields[2]),
            "sta": fields[3],
            "acnt": int(fields[4]),
        }
    except Exception:
        return None

def parse_cwmsg_line(line: str) -> Optional[Dict[str, Any]]:
    if not line.startswith("+CWMSG"):
        return None
    payload = line.split(":", 1)[1].strip()
    fields = _split_csv(payload)
    if len(fields) < 3:
        return None
    msg_id = int(fields[0]) if fields[0].isdigit() else None
    msg_type = fields[2]
    type_def = CWMSG_DEFS.get(msg_type, {})
    param_names = type_def.get("params", [])
    raw_params = fields[3:]
    params: Dict[str, Any] = {}
    for idx, val in enumerate(raw_params):
        name = param_names[idx] if idx < len(param_names) else f"p{idx+1}"
        params[name] = int(val) if val.isdigit() else val
    return {
        "msg_id": msg_id,
        "ts": fields[1],
        "type": msg_type,
        "type_desc": type_def.get("desc", msg_type),
        "params": params,
    }

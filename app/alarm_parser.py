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

# Mapping of alarm codes to categories and Chinese descriptions
ALARM_CODE_DEFS: Dict[int, Dict[str, str]] = {
    100: {"category": "医疗", "desc": "医疗求助"},
    101: {"category": "医疗", "desc": "个人紧急按钮（医疗）"},
    110: {"category": "火警", "desc": "火警"},
    111: {"category": "火警", "desc": "烟感"},
    112: {"category": "火警", "desc": "燃烧"},
    113: {"category": "火警", "desc": "水满"},
    114: {"category": "火警", "desc": "高温"},
    115: {"category": "火警", "desc": "警报箱"},
    116: {"category": "火警", "desc": "管道"},
    117: {"category": "火警", "desc": "火焰"},
    118: {"category": "火警", "desc": "危险"},
    120: {"category": "紧急", "desc": "紧急按钮"},
    121: {"category": "紧急", "desc": "挟持"},
    122: {"category": "紧急", "desc": "24小时无声"},
    123: {"category": "紧急", "desc": "24小时有声"},
    124: {"category": "紧急", "desc": "挟持进入允许"},
    125: {"category": "紧急", "desc": "挟持外出允许"},
    130: {"category": "盗警", "desc": "盗警"},
    131: {"category": "盗警", "desc": "周界"},
    132: {"category": "盗警", "desc": "内部"},
    133: {"category": "盗警", "desc": "24小时（盗窃）"},
    134: {"category": "盗警", "desc": "出入口"},
    135: {"category": "盗警", "desc": "日夜"},
    137: {"category": "盗警", "desc": "防拆"},
    138: {"category": "盗警", "desc": "接近"},
    139: {"category": "盗警", "desc": "交叉防区报警"},
    140: {"category": "通用警情", "desc": "通用报警"},
    142: {"category": "通用警情", "desc": "总线故障"},
    143: {"category": "通用警情", "desc": "扩充设备故障"},
    144: {"category": "通用警情", "desc": "探测器防拆"},
    145: {"category": "通用警情", "desc": "扩充设备防拆"},
    146: {"category": "通用警情", "desc": "无声盗警"},
    150: {"category": "24小时非盗警", "desc": "24小时非盗警"},
    151: {"category": "24小时非盗警", "desc": "燃气"},
    152: {"category": "24小时非盗警", "desc": "冷却"},
    153: {"category": "24小时非盗警", "desc": "失温"},
    154: {"category": "24小时非盗警", "desc": "漏水"},
    155: {"category": "24小时非盗警", "desc": "箔片破坏"},
    156: {"category": "24小时非盗警", "desc": "日间故障"},
    157: {"category": "24小时非盗警", "desc": "气体不足"},
    158: {"category": "24小时非盗警", "desc": "高温"},
    159: {"category": "24小时非盗警", "desc": "低温"},
    161: {"category": "24小时非盗警", "desc": "气流损失"},
    162: {"category": "24小时非盗警", "desc": "一氧化碳"},
    163: {"category": "24小时非盗警", "desc": "水位低"},
    200: {"category": "消防", "desc": "火警监视"},
    201: {"category": "消防", "desc": "水压低"},
    202: {"category": "消防", "desc": "二氧化碳压力低"},
    203: {"category": "消防", "desc": "电子闸门传感"},
    204: {"category": "消防", "desc": "水位低"},
    205: {"category": "消防", "desc": "水泵开启"},
    206: {"category": "消防", "desc": "水泵故障"},
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
        code = int(fields[4])
        rec = {
            "id": int(fields[0]),
            "io": fields[1],
            "ena": int(fields[2]),
            "type": fields[3],
            "code": code,
            "team": int(fields[5]),
            "name": fields[6] if len(fields) > 6 else "",
        }
        code_def = ALARM_CODE_DEFS.get(code)
        if code_def:
            rec["code_desc"] = code_def.get("desc")
            rec["code_type"] = code_def.get("category")
        return rec
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
    if "code" in params and isinstance(params["code"], int):
        code_def = ALARM_CODE_DEFS.get(params["code"])
        if code_def:
            params["code_desc"] = code_def.get("desc")
            params["code_type"] = code_def.get("category")
    return {
        "msg_id": msg_id,
        "ts": fields[1],
        "type": msg_type,
        "type_desc": type_def.get("desc", msg_type),
        "params": params,
    }

from typing import Dict, Any, List, Optional

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
    return {
        "msg_id": int(fields[0]) if fields[0].isdigit() else None,
        "ts": fields[1],
        "type": fields[2],
        "params": fields[3:] if len(fields) > 3 else []
    }

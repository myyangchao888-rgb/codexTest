import socket, threading, time
from typing import Tuple
from . import config, db
from .alarm_parser import parse_dfai_line, parse_dfas_line, parse_cwmsg_line

_last_report_ts = 0.0

def _set_report_ts():
    global _last_report_ts
    _last_report_ts = time.time()

def last_report_time() -> float:
    return _last_report_ts

def handle_client(conn: socket.socket, addr: Tuple[str, int]):
    conn.settimeout(300)
    with conn:
        buff = b""
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    return
                buff += data
                while b"\n" in buff or b"\r" in buff:
                    for sep in (b"\r\n", b"\n", b"\r"):
                        if sep in buff:
                            line, _, buff = buff.partition(sep)
                            break
                    line_s = line.decode(errors="ignore").strip()
                    if not line_s:
                        continue
                    _set_report_ts()
                    rec = parse_dfai_line(line_s)
                    if rec:
                        if "_schema" not in rec:
                            db.upsert_zone(rec)
                        continue
                    rec = parse_dfas_line(line_s)
                    if rec:
                        if "_schema" not in rec:
                            db.upsert_zone_status(rec)
                        continue
                    evt = parse_cwmsg_line(line_s)
                    if evt:
                        db.insert_event(evt.get("ts",""), evt.get("type",""),
                                        ",".join(evt.get("params", [])), line_s)
                        continue
                    if line_s == "AT":
                        conn.sendall(b"OK\r\n")
                    elif line_s == "ATI":
                        conn.sendall(b"ID:SERVER\r\nOEM:CUSTOM\r\nMODEL:PY-SERVER\r\nVERSION:1.0\r\nOK\r\n")
                    elif line_s.startswith("AT+AUTH"):
                        conn.sendall(b"+AUTH: SERVER_AUTH_ID\r\nOK\r\n")
                    else:
                        conn.sendall(b"OK\r\n")
            except socket.timeout:
                continue
            except Exception:
                return

def start_tcp_server():
    db.init_tables()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((config.TCP_HOST, config.TCP_PORT))
    srv.listen(20)
    print(f"[TCP] Listening on {config.TCP_HOST}:{config.TCP_PORT}")
    while True:
        conn, addr = srv.accept()
        print(f"[TCP] Client connected: {addr}")
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

import socket
import threading
import time
import logging
from typing import Tuple, Optional, List
from . import config, data_store
from .alarm_parser import parse_dfai_line, parse_dfas_line, parse_cwmsg_line

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _debug(msg: str, *args) -> None:
    logger.debug(msg, *args)
    if logger.isEnabledFor(logging.DEBUG):
        try:
            print("[DEBUG]", msg % args if args else msg)
        except Exception:
            print("[DEBUG]", msg, *args)


_clients: dict[str, socket.socket] = {}
_last_report_ts: dict[str, float] = {}
_conn_lock = threading.Lock()


def _send_cmd(host_id: str, cmd: str) -> bool:
    with _conn_lock:
        conn = _clients.get(host_id)
    if not conn:
        return False
    try:
        conn.sendall((cmd + "\r\n").encode())
        _debug("Sent to %s: %s", host_id, cmd)
        return True
    except Exception:
        _debug("Failed send to %s: %s", host_id, cmd)
        return False


def arm_zone(host_id: str, zone_id: int) -> bool:
    if _send_cmd(host_id, f"AT+ARM={zone_id},1"):
        data_store.set_zone_arm(host_id, zone_id, 1)
        return True
    return False


def disarm_zone(host_id: str, zone_id: int) -> bool:
    if _send_cmd(host_id, f"AT+ARM={zone_id},0"):
        data_store.set_zone_arm(host_id, zone_id, 0)
        return True
    return False


def arm_host(host_id: str) -> bool:
    return _send_cmd(host_id, "AT+CARM=1")


def disarm_host(host_id: str) -> bool:
    return _send_cmd(host_id, "AT+CDAM=1")


def last_report_time(host_id: str) -> float:
    return _last_report_ts.get(host_id, 0.0)


def _set_report_ts(host_id: str) -> None:
    _last_report_ts[host_id] = time.time()


def connected_hosts() -> List[str]:
    with _conn_lock:
        return list(_clients.keys())


def log_http_data(host_id: str) -> None:
    snapshot = {
        "zones": data_store.fetch_zones(host_id),
        "zone_status": data_store.fetch_zone_status(host_id),
        "events": data_store.fetch_events(host_id),
        "host_info": data_store.fetch_host_info(host_id),
    }
    logger.info("HTTP snapshot[%s]: %s", host_id, snapshot)
    _debug("HTTP snapshot[%s]: %s", host_id, snapshot)


def _send_raw(conn: socket.socket, cmd: str) -> bool:
    try:
        conn.sendall((cmd + "\r\n").encode())
        _debug("Sent command: %s", cmd)
        return True
    except Exception:
        _debug("Failed to send command: %s", cmd)
        return False


def handle_client(conn: socket.socket, addr: Tuple[str, int]):
    logger.info("Client connected: %s", addr)
    conn.settimeout(300)
    stop_keepalive = threading.Event()
    host_id: Optional[str] = None

    def keepalive_loop() -> None:
        while not stop_keepalive.is_set() and host_id:
            if not _send_cmd(host_id, "AT+CWMSG="):
                break
            for _ in range(int(config.CWMSG_KEEPALIVE_SEC)):
                if stop_keepalive.is_set():
                    return
                time.sleep(1)

    try:
        with conn:
            _send_raw(conn, "ATI")
            time.sleep(0.1)
            _send_raw(conn, "AT+AUTH=")
            time.sleep(0.1)
            _send_raw(conn, "AT+CWMSG=SET,0,0,60,5,1,1")
            time.sleep(0.1)
            _send_raw(conn, "AT+DFAI?")
            time.sleep(0.1)
            _send_raw(conn, "AT+DFAI=")
            time.sleep(0.1)
            _send_raw(conn, "AT+DFAS?")
            time.sleep(0.1)
            _send_raw(conn, "AT+DFAS=")

            buff = b""
            keepalive_started = False
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
                        logger.info("Device data: %s", line_s)
                        _debug("Raw line: %s", line_s)
                        if host_id:
                            _set_report_ts(host_id)
                        if line_s.startswith("ID:"):
                            host_id = line_s.split(":", 1)[1].strip()
                            data_store.set_host_info(host_id, "id", host_id)
                            with _conn_lock:
                                _clients[host_id] = conn
                            if not keepalive_started:
                                threading.Thread(target=keepalive_loop, daemon=True).start()
                                keepalive_started = True
                            continue
                        if not host_id:
                            continue
                        if line_s.startswith("OEM:"):
                            data_store.set_host_info(host_id, "oem", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("MODEL:"):
                            data_store.set_host_info(host_id, "model", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("VERSION:"):
                            data_store.set_host_info(host_id, "version", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("+AUTH:"):
                            data_store.set_host_info(host_id, "auth_code", line_s.split(":", 1)[1].strip())
                            continue
                        rec = parse_dfai_line(line_s)
                        if rec:
                            logger.info("DFAI[%s]: %s", host_id, rec)
                            _debug("Parsed DFAI: %s", rec)
                            if "_schema" in rec:
                                data_store.set_zone_schema(host_id, rec["_schema"])
                            else:
                                data_store.upsert_zone(host_id, rec)
                            continue
                        rec = parse_dfas_line(line_s)
                        if rec:
                            logger.info("DFAS[%s]: %s", host_id, rec)
                            _debug("Parsed DFAS: %s", rec)
                            if "_schema" in rec:
                                data_store.set_zone_status_schema(host_id, rec["_schema"])
                            else:
                                data_store.upsert_zone_status(host_id, rec)
                            continue
                        evt = parse_cwmsg_line(line_s)
                        if evt:
                            logger.info("CWMSG[%s]: %s", host_id, evt)
                            _debug("Parsed CWMSG: %s", evt)
                            data_store.add_event(host_id, evt, line_s)
                            msg_id = evt.get("msg_id")
                            if msg_id is not None:
                                _send_cmd(host_id, f"AT+CWMSG={msg_id}")
                            continue
                        if line_s == "AT":
                            conn.sendall(b"OK\r\n")
                        elif line_s == "ATI":
                            conn.sendall(b"ID:SERVER\r\nOEM:CUSTOM\r\nMODEL:PY-SERVER\r\nVERSION:1.0\r\nOK\r\n")
                        elif line_s.startswith("AT+AUTH"):
                            conn.sendall(b"+AUTH: SERVER_AUTH_ID\r\nOK\r\n")
                        else:
                            logger.info("Unhandled line[%s]: %s", host_id, line_s)
                            _debug("Unhandled line: %s", line_s)
                            conn.sendall(b"OK\r\n")
                except socket.timeout:
                    continue
                except Exception:
                    logger.exception("Error handling client %s", addr)
                    return
    finally:
        stop_keepalive.set()
        if host_id:
            with _conn_lock:
                _clients.pop(host_id, None)


def start_tcp_server() -> None:
    """Start the TCP server and accept incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((config.TCP_HOST, config.TCP_PORT))
    server.listen()
    logger.info("Listening on %s:%s", config.TCP_HOST, config.TCP_PORT)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

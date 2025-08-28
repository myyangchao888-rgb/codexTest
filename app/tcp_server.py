import socket, threading, time, logging
from typing import Tuple, Optional
from . import config, data_store
from .alarm_parser import parse_dfai_line, parse_dfas_line, parse_cwmsg_line

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _debug(msg: str, *args) -> None:
    """Log and print debug messages to the console."""
    logger.debug(msg, *args)
    if logger.isEnabledFor(logging.DEBUG):
        try:
            print("[DEBUG]" , msg % args if args else msg)
        except Exception:
            # Fallback in case of formatting issues
            print("[DEBUG]", msg, *args)

_last_report_ts = 0.0
_client_conn: Optional[socket.socket] = None
_conn_lock = threading.Lock()

def _set_report_ts():
    global _last_report_ts
    _last_report_ts = time.time()

def last_report_time() -> float:
    return _last_report_ts

def _set_client(conn: Optional[socket.socket]) -> None:
    global _client_conn
    with _conn_lock:
        _client_conn = conn


def _send_cmd(cmd: str) -> bool:
    with _conn_lock:
        if not _client_conn:
            return False
        try:
            _client_conn.sendall((cmd + "\r\n").encode())
            _debug("Sent command: %s", cmd)
            return True
        except Exception:
            _debug("Failed to send command: %s", cmd)
            return False


def arm_zone(zone_id: int) -> bool:
    if _send_cmd(f"AT+ARM={zone_id},1"):
        data_store.set_zone_arm(zone_id, 1)
        return True
    return False


def disarm_zone(zone_id: int) -> bool:
    if _send_cmd(f"AT+ARM={zone_id},0"):
        data_store.set_zone_arm(zone_id, 0)
        return True
    return False


def arm_host() -> bool:
    return _send_cmd("AT+CARM=1")


def disarm_host() -> bool:
    return _send_cmd("AT+CDAM=1")


def log_http_data() -> None:
    """Print a snapshot of data exposed via HTTP endpoints."""
    snapshot = {
        "zones": data_store.fetch_zones(),
        "zone_status": data_store.fetch_zone_status(),
        "events": data_store.fetch_events(),
        "host_info": data_store.fetch_host_info(),
    }
    logger.info("HTTP snapshot: %s", snapshot)
    _debug("HTTP snapshot: %s", snapshot)


def handle_client(conn: socket.socket, addr: Tuple[str, int]):
    logger.info("Client connected: %s", addr)
    _set_client(conn)
    conn.settimeout(300)
    stop_keepalive = threading.Event()

    def keepalive_loop():
        while not stop_keepalive.is_set():
            if not _send_cmd("AT+CWMSG="):
                break
            for _ in range(int(config.CWMSG_KEEPALIVE_SEC)):
                if stop_keepalive.is_set():
                    return
                time.sleep(1)

    try:
        with conn:
            if _send_cmd("ATI"):
                logger.info("Sent ATI to client %s", addr)
            else:
                logger.warning("Failed to send ATI to client %s", addr)
            time.sleep(0.1)
            _send_cmd("AT+AUTH=")
            time.sleep(0.1)
            _send_cmd("AT+CWMSG=SET,0,0,60,5,1,1")
            # Query zone information and status on connect
            time.sleep(0.1)
            _send_cmd("AT+DFAI?")
            time.sleep(0.1)
            _send_cmd("AT+DFAI=")
            time.sleep(0.1)
            _send_cmd("AT+DFAS?")
            time.sleep(0.1)
            _send_cmd("AT+DFAS=")

            threading.Thread(target=keepalive_loop, daemon=True).start()
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
                        logger.info("Device data: %s", line_s)
                        _debug("Raw line: %s", line_s)
                        _set_report_ts()
                        if line_s.startswith("ID:"):
                            data_store.set_host_info("id", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("OEM:"):
                            data_store.set_host_info("oem", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("MODEL:"):
                            data_store.set_host_info("model", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("VERSION:"):
                            data_store.set_host_info("version", line_s.split(":", 1)[1].strip())
                            continue
                        if line_s.startswith("+AUTH:"):
                            data_store.set_host_info("auth_code", line_s.split(":", 1)[1].strip())
                            continue
                        rec = parse_dfai_line(line_s)
                        if rec:
                            logger.info("DFAI: %s", rec)
                            _debug("Parsed DFAI: %s", rec)
                            if "_schema" in rec:
                                data_store.set_zone_schema(rec["_schema"])
                            else:
                                data_store.upsert_zone(rec)
                            continue
                        rec = parse_dfas_line(line_s)
                        if rec:
                            logger.info("DFAS: %s", rec)
                            _debug("Parsed DFAS: %s", rec)
                            if "_schema" in rec:
                                data_store.set_zone_status_schema(rec["_schema"])
                            else:
                                data_store.upsert_zone_status(rec)
                            continue
                        evt = parse_cwmsg_line(line_s)
                        if evt:
                            logger.info("CWMSG: %s", evt)
                            _debug("Parsed CWMSG: %s", evt)
                            data_store.add_event(evt, line_s)
                            msg_id = evt.get("msg_id")
                            if msg_id is not None:
                                _send_cmd(f"AT+CWMSG={msg_id}")
                            continue
                        if line_s == "AT":
                            conn.sendall(b"OK\r\n")
                        elif line_s == "ATI":
                            conn.sendall(b"ID:SERVER\r\nOEM:CUSTOM\r\nMODEL:PY-SERVER\r\nVERSION:1.0\r\nOK\r\n")
                        elif line_s.startswith("AT+AUTH"):
                            conn.sendall(b"+AUTH: SERVER_AUTH_ID\r\nOK\r\n")
                        else:
                            logger.info("Unhandled line: %s", line_s)
                            _debug("Unhandled line: %s", line_s)
                            conn.sendall(b"OK\r\n")
                except socket.timeout:
                    continue
                except Exception:
                    logger.exception("Error handling client %s", addr)
                    return
    finally:
        _set_client(None)
        stop_keepalive.set()

def start_tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((config.TCP_HOST, config.TCP_PORT))
    srv.listen(20)
    logger.info("Listening on %s:%s", config.TCP_HOST, config.TCP_PORT)
    while True:
        conn, addr = srv.accept()
        logger.info("Accepted connection from %s", addr)
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

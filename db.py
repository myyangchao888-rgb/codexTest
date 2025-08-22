import pymysql
from typing import List, Dict, Any
from . import config

def get_conn():
    return pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )

def init_tables():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id INT PRIMARY KEY,
            io VARCHAR(16),
            ena TINYINT,
            type INT,
            code INT,
            team INT,
            name VARCHAR(128)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS zone_status (
            id INT PRIMARY KEY,
            arm TINYINT,
            bypass TINYINT,
            sta VARCHAR(32),
            acnt INT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS host_events (
            msg_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            ts VARCHAR(32),
            type VARCHAR(64),
            params TEXT,
            raw TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.close()

def upsert_zone(rec: Dict[str, Any]):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO zones (id, io, ena, type, code, team, name)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE io=VALUES(io), ena=VALUES(ena), type=VALUES(type),
            code=VALUES(code), team=VALUES(team), name=VALUES(name);
        """, (
            rec.get("id"), rec.get("io"), rec.get("ena"), rec.get("type"),
            rec.get("code"), rec.get("team"), rec.get("name")
        ))
    conn.close()

def upsert_zone_status(rec: Dict[str, Any]):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO zone_status (id, arm, bypass, sta, acnt)
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE arm=VALUES(arm), bypass=VALUES(bypass), sta=VALUES(sta), acnt=VALUES(acnt);
        """, (
            rec.get("id"), rec.get("arm"), rec.get("bypass"), rec.get("sta"), rec.get("acnt")
        ))
    conn.close()

def insert_event(ts: str, typ: str, params: str, raw: str):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO host_events (ts, type, params, raw) VALUES (%s,%s,%s,%s);
        """, (ts, typ, params, raw))
    conn.close()

def fetch_zones() -> List[Dict[str, Any]]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM zones ORDER BY id ASC;")
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_zone_status() -> List[Dict[str, Any]]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM zone_status ORDER BY id ASC;")
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_events(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM host_events ORDER BY create_time DESC LIMIT %s;", (limit,))
        rows = cur.fetchall()
    conn.close()
    return rows

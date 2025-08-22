import threading, uvicorn, time
from app import config
from app.tcp_server import start_tcp_server
from app.api import app as api_app

def run_tcp():
    start_tcp_server()

def run_api():
    uvicorn.run(api_app, host=config.API_HOST, port=config.API_PORT, log_level="info")

if __name__ == "__main__":
    t = threading.Thread(target=run_tcp, daemon=True)
    t.start()
    time.sleep(0.5)
    run_api()

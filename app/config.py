import os
from dotenv import load_dotenv

load_dotenv()

TCP_HOST = os.getenv("TCP_HOST", "0.0.0.0")
TCP_PORT = int(os.getenv("TCP_PORT", "8899"))

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

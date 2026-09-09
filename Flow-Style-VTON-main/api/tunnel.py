"""
Flow-Style-VTON ngrok Tunnel Utility
Exposes FastAPI on port 8000 via a secure public HTTPS URL.
"""

import os
import sys
import time
import requests
from pyngrok import ngrok, conf

PORT = int(os.getenv("PORT", 8000))
AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", None)


def start_tunnel(authtoken: str = None, port: int = PORT):
    token = authtoken or AUTHTOKEN
    if not token:
        print("[-] ERROR: NGROK_AUTHTOKEN is required to establish an ngrok tunnel.")
        print("    Set it via environment variable: export NGROK_AUTHTOKEN=your_token")
        print("    Or pass it as argument: python tunnel.py --token your_token")
        sys.exit(1)

    print("[*] Setting ngrok authtoken...")
    conf.get_default().auth_token = token

    print(f"[*] Opening ngrok HTTP tunnel to port {port}...")
    tunnel = ngrok.connect(port, "http")
    public_url = tunnel.public_url.replace("http://", "https://")
    print("=" * 60)
    print(f"[+] NGROK TUNNEL ONLINE: {public_url}")
    print(f"    Health:  {public_url}/health")
    print(f"    Swagger: {public_url}/docs")
    print(f"    Try-On:  {public_url}/tryon")
    print("=" * 60)

    # Quick self-check
    try:
        print("[*] Verifying public endpoint health...")
        resp = requests.get(f"{public_url}/health", timeout=10)
        print(f"    Health response: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"    Warning: Public health check deferred: {e}")

    return public_url


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start ngrok tunnel for Flow-Style-VTON API")
    parser.add_argument("--token", type=str, default=None, help="ngrok authtoken")
    parser.add_argument("--port", type=int, default=PORT, help="FastAPI port (default 8000)")
    args = parser.parse_args()

    url = start_tunnel(args.token, args.port)
    print("\nTunnel running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing tunnel...")
        ngrok.kill()

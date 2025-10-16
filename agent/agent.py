import os
import psutil
import requests
import time
import json
import socket
import sys
from datetime import datetime

# --- Individual Metric Collector Functions ---

def get_cpu_percent():
    return psutil.cpu_percent(interval=1)

def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent_used": mem.percent
    }

def get_disk_info(path='/'):
    disk = psutil.disk_usage(path)
    return {
        "total_gb": round(disk.total / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "percent_used": disk.percent
    }

def get_network_io():
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_received": net.bytes_recv
    }

def get_load_average():
    load_1m, load_5m, load_15m = psutil.getloadavg()
    cpu_count = psutil.cpu_count()
    return {
        "1m": load_1m,
        "5m": load_5m,
        "15m": load_15m,
        "1m_normalized": round(load_1m / cpu_count, 2),
        "5m_normalized": round(load_5m / cpu_count, 2),
        "15m_normalized": round(load_15m / cpu_count, 2)
    }

class SysSightAgent:
    def __init__(self):
        self.server_url = os.getenv("SYSSIGHT_SERVER_URL", "http://127.0.0.1:8000/metrics")
        self.interval = int(os.getenv("SYSSIGHT_INTERVAL", 10))
        self.auth_token = os.getenv("SYSSIGHT_AUTH_TOKEN", "your_secret_auth_token")
        self.hostname = socket.gethostname()

        self.metric_collectors = {
            "cpu_percent": get_cpu_percent,
            "memory": get_memory_info,
            "disk": get_disk_info,
            "network": get_network_io,
            "load_average": get_load_average,
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        })

    def collect_metrics(self):
        payload = {
            "hostname": self.hostname,
            "timestamp": datetime.utcnow().isoformat() + "Z", # ISO 8601 format
        }
        
        for name, collector_func in self.metric_collectors.items():
            try:
                payload[name] = collector_func()
            except Exception as e:
                print(f"Error collecting metric '{name}': {e}", file=sys.stderr)
                payload[name] = None # Report failure for this specific metric.

        return payload

    def run(self):
        print("Starting SysSight Agent...")
        print(f"   Host: {self.hostname}")
        print(f"   Pushing to: {self.server_url}")
        print(f"   Interval: {self.interval} seconds")

        while True:
            try:
                start_time = time.time()
                
                # 1. Collect all metrics.
                metrics_payload = self.collect_metrics()
                
                print("\n" + "="*50)
                print(f"Collected at {metrics_payload['timestamp']}:")
                print(json.dumps(metrics_payload, indent=2))

                # 2. Push metrics to the server.
                response = self.session.post(
                    self.server_url, 
                    data=json.dumps(metrics_payload),
                    timeout=5
                )
                response.raise_for_status() 
                
                print(f"Successfully pushed metrics. Server responded with: {response.status_code}")

            except requests.exceptions.HTTPError as e:
                print(f"Error: HTTP Error {e.response.status_code}. The server rejected the data.", file=sys.stderr)
                try:
                    print(f"   Server says: {e.response.json()}", file=sys.stderr)
                except json.JSONDecodeError:
                    print(f"   Could not decode server's JSON response.", file=sys.stderr)
            
            except requests.exceptions.RequestException as e:
                print(f"Error: Could not push metrics. Check server connection.", file=sys.stderr)
                print(f"   Details: {e}", file=sys.stderr)
            
            # 3. Wait for the next interval.
            elapsed_time = time.time() - start_time
            sleep_duration = max(0, self.interval - elapsed_time)
            time.sleep(sleep_duration)

if __name__ == "__main__":
    agent = SysSightAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\nAgent shutdown requested. Exiting gracefully.")
        sys.exit(0)
import os
import psutil
import requests
import time
import json
import socket
import sys
import threading
from datetime import datetime
from flask import Flask, jsonify

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

def get_process_list():
    """
    Collect running processes with pid, name, cpu_percent, and memory_percent.
    Handles permission errors gracefully.
    """
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                process_info = proc.info
                processes.append({
                    "pid": process_info['pid'],
                    "name": process_info['name'],
                    "cpu_percent": round(process_info['cpu_percent'] or 0, 2),
                    "memory_percent": round(process_info['memory_percent'] or 0, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes that no longer exist, are inaccessible, or are zombie processes
                continue
    except Exception as e:
        print(f"Error collecting process list: {e}", file=sys.stderr)
    
    return processes

class SysSightAgent:
    def __init__(self):
        self.server_url = os.getenv("SYSSIGHT_SERVER_URL", "http://127.0.0.1:8000/metrics")
        self.interval = int(os.getenv("SYSSIGHT_INTERVAL", 10))
        self.auth_token = os.getenv("SYSSIGHT_AUTH_TOKEN", "your_secret_auth_token")
        self.hostname = socket.gethostname()
        self.flask_port = int(os.getenv("SYSSIGHT_FLASK_PORT", 9090))
        
        # Get IP address for agent registration
        self.ip_address = self._get_ip_address()

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
        
        # Initialize Flask app for process serving
        self.flask_app = Flask(__name__)
        self._setup_flask_routes()

    def _get_ip_address(self):
        """Get the primary IP address with robust fallbacks."""
        try:
            # Preferred: determine outbound interface IP without sending data
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "unknown"

    def _setup_flask_routes(self):
        """Setup Flask routes for process serving."""
        @self.flask_app.route('/processes', methods=['GET'])
        def get_processes():
            try:
                processes = get_process_list()
                return jsonify(processes)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def register_with_server(self):
        """Register this agent with the main server."""
        try:
            registration_url = self.server_url.replace('/metrics', '/api/v1/agents/register')
            registration_data = {
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "port": self.flask_port
            }
            
            response = self.session.post(
                registration_url,
                data=json.dumps(registration_data),
                timeout=5
            )
            response.raise_for_status()
            print(f"Successfully registered with server: {self.hostname} -> {self.ip_address}:{self.flask_port}")
            return True
        except Exception as e:
            print(f"Failed to register with server: {e}", file=sys.stderr)
            return False

    def start_flask_server(self):
        """Start Flask server in a separate thread."""
        def run_flask():
            self.flask_app.run(host='0.0.0.0', port=self.flask_port, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print(f"Flask server started on port {self.flask_port}")

    def collect_metrics(self):
        # Get primary IP address with robust fallbacks
        ip_address = "unknown"
        try:
            # Preferred: determine outbound interface IP without sending data
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
        except Exception:
            try:
                ip_address = socket.gethostbyname(socket.gethostname())
            except Exception:
                ip_address = "unknown"
        
        payload = {
            "hostname": self.hostname,
            "timestamp": datetime.utcnow().isoformat() + "Z", # ISO 8601 format
            "ip_address": ip_address,
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
        print(f"   IP: {self.ip_address}")
        print(f"   Pushing to: {self.server_url}")
        print(f"   Flask port: {self.flask_port}")
        print(f"   Interval: {self.interval} seconds")

        # Start Flask server in background thread
        self.start_flask_server()
        
        # Register with main server
        print("Registering with main server...")
        self.register_with_server()

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
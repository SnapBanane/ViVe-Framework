import os
import sys
import time
import threading
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from vive.modules.webserver.server import WebServer
from vive.modules.portManager.manager import PortManager
from vive.modules.webcam.webcam_streamer import WebcamStreamer

console = Console()
VIVE_ENV_PATH = os.path.join(os.path.dirname(__file__), "vive", ".env")

class ViveServer:
    def __init__(self):
        self.web_server = None
        self.port_manager = PortManager()
        self.webcam_streamer = WebcamStreamer(vive_server=self)
        self.services = {
            "webserver": {"status": "stopped", "port": 5000, "instance": None},
            "port_manager": {"status": "stopped", "port": None, "instance": self.port_manager},
            "webcam_streamer": {"status": "stopped", "instance": self.webcam_streamer}
        }
        self.logs = []
        self.config = {}
        self.port_manager.set_logger(self.log)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 50:
            self.logs.pop(0)
        console.print(log_entry)

    def load_config(self):
        if not os.path.exists(VIVE_ENV_PATH):
            self.log(f"Config file not found at {VIVE_ENV_PATH}", "WARN")
            return {}
        load_dotenv(VIVE_ENV_PATH)
        self.config = {k: v for k, v in os.environ.items() if k.startswith("UNTIS") or k.startswith("VIVE")}
        self.log(f"Loaded {len(self.config)} config items")
        return self.config

    def start_web_server(self):
        try:
            if self.services["webserver"]["status"] == "running":
                self.log("Web server already running", "WARN")
                return
            def run_web():
                self.web_server = WebServer(port=self.services["webserver"]["port"], vive_server=self)
                self.web_server.start()
            t = threading.Thread(target=run_web, daemon=True)
            t.start()
            self.services["webserver"]["status"] = "running"
            self.services["webserver"]["instance"] = self.web_server
            self.log(f"Web server started on port {self.services['webserver']['port']}")
            # Initialize the webcam streamer with the server instance
            from vive.modules.webserver.app import initialize_webcam_streamer
            initialize_webcam_streamer(self)
        except Exception as e:
            self.log(f"Failed to start web server: {e}", "ERROR")
            self.services["webserver"]["status"] = "error"

    def log_client_connection(self, client_ip):
        self.log(f"Client connected from {client_ip}", "INFO")

    def start_port_manager(self):
        try:
            if self.services["port_manager"]["status"] == "running":
                self.log("Port Manager is already running.", "WARN")
                return
            # Start port manager in a background thread, independent of webserver status
            def run_port():
                self.port_manager.internal_port = self.services["webserver"]["port"]
                self.port_manager.setup_port_forwarding()
            t = threading.Thread(target=run_port, daemon=True)
            t.start()
            self.services["port_manager"]["status"] = "running"
            self.log("Port Manager started. Attempting to forward port.")
            time.sleep(2)
            local_ip = self.port_manager.get_local_ip()
            self.log(f"Server accessible on your local network at http://{local_ip}:{self.services['webserver']['port']}", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to start Port Manager: {e}", "ERROR")
            self.services["port_manager"]["status"] = "error"

    def start_all_services(self):
        self.log("Starting all services...")
        self.start_web_server()
        self.start_port_manager()
        self.log("All services started successfully.")

    def stop_services(self):
        """Stops all running services."""
        self.log("Stopping services...", "INFO")
        if self.web_server:
            self.web_server.stop()
        if self.webcam_streamer:
            asyncio.run(self.webcam_streamer.close())
        if self.port_manager:
            # Assuming the port manager has a similar stop method if needed.
            # For now, we rely on daemon threads terminating with the app.
            pass
        self.log("All services stopped.", "INFO")

    def run(self):
        """Main server loop."""
        self.start_services()
        try:
            while True:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            self.log("Shutting down server...", "INFO")
            self.stop_services()

if __name__ == "__main__":
    server = ViveServer()
    server.load_config()
    server.start_all_services()
    while True:
        time.sleep(60)  # Keep the process alive
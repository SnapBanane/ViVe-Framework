import os
import sys
import threading
import time
import logging
import requests
from .app import app
from waitress import serve
from zeroconf import ServiceInfo, Zeroconf
import socket

# Completely suppress all Flask/Werkzeug output
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
logging.getLogger('flask').setLevel(logging.CRITICAL)

class WebServer:
    def __init__(self, host='0.0.0.0', port=2525, vive_server=None):
        self.host = host
        self.port = port
        self.vive_server = vive_server
        self.thread = None
        self.zeroconf = None
        self.service_info = None
    
    def start(self):
        """Start the web server in a separate thread - SILENTLY"""
        if self.running:
            return
        
        # Register mDNS service before starting the server
        self._register_mdns_service()
        
        self.running = True
        self.thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.thread.start()
        
        # Wait for server to start
        time.sleep(2)
    
    def _run_server(self):
        """Run Flask app with output NOT suppressed (for logging)"""
        try:
            # Do NOT redirect sys.stdout/sys.stderr so logging works
            app.config['VIVE_SERVER'] = self.vive_server
            app.run(
                host=self.host,
                port=self.port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            print(f"WebServer critical error: {e}", file=sys.__stderr__)
    
    def stop(self):
        """Stop the web server by sending a shutdown request."""
        if not self.running:
            return
        self.running = False
        try:
            # Send a request to the shutdown route to stop Werkzeug
            requests.post(f"http://{self.host}:{self.port}/shutdown", timeout=1)
        except requests.exceptions.RequestException:
            # This is expected as the server will shut down
            pass
        finally:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2) # Wait for thread to terminate
            self._unregister_mdns_service()

    
    def is_running(self):
        """Check if server is running"""
        return self.running and self.thread and self.thread.is_alive()

    def _get_local_ip(self):
        """Helper to get the local IP address for mDNS registration."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def _register_mdns_service(self):
        """Registers the web server as a service using mDNS/Bonjour."""
        try:
            ip_address = self._get_local_ip()
            service_name = "ViVe Framework"
            service_type = "_http._tcp.local."
            service_port = self.port
            server_name = "vive.local."  # The friendly hostname

            self.zeroconf = Zeroconf()
            
            self.service_info = ServiceInfo(
                service_type,
                f"{service_name}.{service_type}",
                addresses=[socket.inet_aton(ip_address)],
                port=service_port,
                properties={'path': '/mobile'}, # Point to mobile page
                server=server_name,
            )
            
            self.zeroconf.register_service(self.service_info)
            if self.vive_server:
                self.vive_server.log(f"mDNS service '{service_name}' registered as http://vive.local:{service_port}", "INFO")

        except Exception as e:
            if self.vive_server:
                self.vive_server.log(f"Could not start mDNS service: {e}", "ERROR")

    def start(self):
        """Starts the web server in a separate thread."""
        # Register mDNS service before starting the server
        self._register_mdns_service()
        
        def worker():
            # Use waitress for a production-ready server, but disable its default logger
            # to avoid interfering with the main server's logging setup.
            logger = logging.getLogger('waitress')
            logger.setLevel(logging.ERROR) # Only show errors from waitress
            serve(app, host=self.host, port=self.port)

        self.thread = threading.Thread(target=worker)
        self.thread.daemon = True  # Ensures thread exits when main program does
        self.thread.start()
        if self.vive_server:
            self.vive_server.log(f"Web server started at http://{self.host}:{self.port}", "INFO")

    def stop(self):
        """Stops the mDNS service."""
        if not self.running:
            return
        self.running = False
        try:
            # Send a request to the shutdown route to stop Werkzeug
            requests.post(f"http://{self.host}:{self.port}/shutdown", timeout=1)
        except requests.exceptions.RequestException:
            # This is expected as the server will shut down
            pass
        finally:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2) # Wait for thread to terminate
            self._unregister_mdns_service()

    
    def is_running(self):
        """Check if server is running"""
        return self.running and self.thread and self.thread.is_alive()

    def _get_local_ip(self):
        """Helper to get the local IP address for mDNS registration."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def _register_mdns_service(self):
        """Registers the web server as a service using mDNS/Bonjour."""
        try:
            ip_address = self._get_local_ip()
            service_name = "ViVe Framework"
            service_type = "_http._tcp.local."
            service_port = self.port
            server_name = "vive.local."  # The friendly hostname

            self.zeroconf = Zeroconf()
            
            self.service_info = ServiceInfo(
                service_type,
                f"{service_name}.{service_type}",
                addresses=[socket.inet_aton(ip_address)],
                port=service_port,
                properties={'path': '/mobile'}, # Point to mobile page
                server=server_name,
            )
            
            self.zeroconf.register_service(self.service_info)
            if self.vive_server:
                self.vive_server.log(f"mDNS service '{service_name}' registered as http://vive.local:{service_port}", "INFO")

        except Exception as e:
            if self.vive_server:
                self.vive_server.log(f"Could not start mDNS service: {e}", "ERROR")

    def _unregister_mdns_service(self):
        """Unregisters the web server mDNS service."""
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                if self.vive_server:
                    self.vive_server.log("mDNS service unregistered.", "INFO")
            except Exception as e:
                if self.vive_server:
                    self.vive_server.log(f"Error stopping mDNS service: {e}", "ERROR")
        # Note: Stopping waitress/Flask programmatically is complex and often not clean.
        # Since the thread is a daemon, it will exit when the main process terminates.
        # This is sufficient for the current design.
        if self.vive_server:
            self.vive_server.log("Web server stopping (daemon thread will terminate with main app).", "INFO")

def run_server(host='0.0.0.0', port=2525):
    """Standalone function to run the server"""
    # Suppress ALL output
    import logging
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
    
    app.run(host=host, port=port, debug=False, threaded=True)
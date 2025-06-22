import socket
import json
import os
import time
import uuid
import threading
import subprocess
import platform
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class PortManager:
    def __init__(self, config_file="port_config.json"):
        self.config_file = config_file
        self.authorized_devices = {}
        self.pending_requests = {}
        self.port_forwarding_active = False
        self.external_port = None
        self.internal_port = 5000
        self.lock = threading.Lock()
        self.MAX_DEVICES = 2
        self.logger = None  # For logging callbacks
        self.load_config()
        
    def set_logger(self, logger_func):
        """Sets a callback function for logging."""
        self.logger = logger_func

    def _log(self, message, level="INFO"):
        """Internal log helper to prevent errors if no logger is set."""
        if self.logger:
            self.logger(message, level)

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.authorized_devices = config.get('authorized_devices', {})
                    self.external_port = config.get('external_port', 8080)
                    self.internal_port = config.get('internal_port', 5000)
            except Exception as e:
                console.print(f"[red]Error loading config: {e}[/red]")
                self.authorized_devices = {}
        else:
            # Create default config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'authorized_devices': self.authorized_devices,
            'external_port': self.external_port,
            'internal_port': self.internal_port,
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to a remote server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def get_public_ip(self):
        """Get public IP address"""
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('origin', 'Unknown')
        except Exception:
            return "Unknown"

    def is_ip_authorized(self, ip_address):
        """Check if a given IP address is in the authorized list."""
        with self.lock:
            for device in self.authorized_devices.values():
                if device.get('ip_address') == ip_address:
                    self._log(f"Authorized access for IP: {ip_address}", "SUCCESS")
                    return True
            self._log(f"Unauthorized access attempt from IP: {ip_address}", "WARN")
            return False

    def is_device_authorized(self, device_id):
        """Check if a given device ID is in the authorized list."""
        with self.lock:
            return device_id in self.authorized_devices

    def request_authorization(self, ip_address, device_name):
        with self.lock:
            self._log(f"Auth request from IP: {ip_address}, Device: {device_name}", "INFO")
            # Check if already authorized
            for device_id, device_info in self.authorized_devices.items():
                if device_info.get('ip_address') == ip_address:
                    self._log(f"IP {ip_address} is already authorized with device ID {device_id}.", "DIM")
                    return device_id

            # Check if already pending
            for device_id, request in self.pending_requests.items():
                if request['ip_address'] == ip_address:
                    self._log(f"IP {ip_address} already has a pending request.", "DIM")
                    return device_id

            device_id = str(uuid.uuid4())
            self.pending_requests[device_id] = {
                "ip_address": ip_address,
                "device_name": device_name,
                "timestamp": time.time()
            }
            return device_id

    def get_pending_requests(self):
        """Return a copy of the pending requests dictionary."""
        with self.lock:
            return dict(self.pending_requests)

    def authorize_device(self, device_id, device_name):
        with self.lock:
            if device_id in self.pending_requests:
                if len(self.authorized_devices) >= self.MAX_DEVICES:
                    # Optional: Evict the oldest device if you want to allow new ones
                    # oldest_device = min(self.authorized_devices.items(), key=lambda x: x[1]['timestamp'])
                    # del self.authorized_devices[oldest_device[0]]
                    console.print(f"[yellow]Cannot authorize new device. Maximum of {self.MAX_DEVICES} devices reached.[/yellow]")
                    return False

                request_info = self.pending_requests.pop(device_id)
                self.authorized_devices[device_id] = {
                    "ip_address": request_info["ip_address"],
                    "device_name": device_name,
                    "timestamp": time.time()
                }
                self.save_config()
                console.print(f"[green]Device {device_name} ({request_info['ip_address']}) authorized.[/green]")
                self._log(f"Device {device_name} ({request_info['ip_address']}) authorized.", "SUCCESS")
                return True
            return False

    def deny_device(self, device_id):
        with self.lock:
            if device_id in self.pending_requests:
                self.pending_requests.pop(device_id)
                self._log(f"Authorization request for device ID {device_id} denied.", "INFO")
                return True
            return False
    
    def setup_port_forwarding(self, external_port=8080):
        """Setup port forwarding using UPnP"""
        self.external_port = external_port
        
        try:
            # Try to use UPnP for automatic port forwarding
            result = self._setup_upnp_forwarding()
            if result:
                self.port_forwarding_active = True
                console.print(f"[green]✅ Port forwarding active: {external_port} -> {self.internal_port}[/green]")
                self._log(f"Port forwarding setup: {external_port} -> {self.internal_port}", "SUCCESS")
                return True
            else:
                console.print("[yellow]⚠ Automatic port forwarding failed. Manual setup required.[/yellow]")
                self._log("Automatic port forwarding failed.", "WARN")
                return False
        except Exception as e:
            console.print(f"[red]Error setting up port forwarding: {e}[/red]")
            self._log(f"Error setting up port forwarding: {e}", "ERROR")
            return False
    
    def _setup_upnp_forwarding(self):
        """Setup UPnP port forwarding"""
        try:
            # Try using upnpc command line tool
            if platform.system() == "Windows":
                # Windows UPnP setup
                return self._windows_upnp_setup()
            else:
                # Linux/Mac UPnP setup
                return self._unix_upnp_setup()
        except Exception as e:
            console.print(f"[red]UPnP setup failed: {e}[/red]")
            self._log(f"UPnP setup failed: {e}", "ERROR")
            return False
    
    def _windows_upnp_setup(self):
        """Windows UPnP setup using netsh"""
        try:
            # Enable UPnP
            subprocess.run(['netsh', 'firewall', 'set', 'portopening', 'tcp', 
                          str(self.external_port), 'ViVeServer', 'enable'], 
                         capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _unix_upnp_setup(self):
        """Unix UPnP setup using upnpc"""
        try:
            # Check if upnpc is available
            subprocess.run(['upnpc', '-a', self.get_local_ip(), 
                          str(self.internal_port), str(self.external_port), 'tcp'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def remove_port_forwarding(self):
        """Remove port forwarding"""
        try:
            if platform.system() == "Windows":
                subprocess.run(['netsh', 'firewall', 'delete', 'portopening', 'tcp', 
                              str(self.external_port)], capture_output=True)
            else:
                subprocess.run(['upnpc', '-d', str(self.external_port), 'tcp'], 
                             capture_output=True)
            
            self.port_forwarding_active = False
            console.print("[yellow]Port forwarding removed[/yellow]")
            self._log(f"Port forwarding removed for external port {self.external_port}.", "INFO")
        except Exception as e:
            console.print(f"[red]Error removing port forwarding: {e}[/red]")
            self._log(f"Error removing port forwarding: {e}", "ERROR")
    
    def show_status(self):
        """Show current port manager status"""
        console.print(Panel(
            f"Local IP: {self.get_local_ip()}\n"
            f"Public IP: {self.get_public_ip()}\n"
            f"Internal Port: {self.internal_port}\n"
            f"External Port: {self.external_port}\n"
            f"Port Forwarding: {'✅ Active' if self.port_forwarding_active else '❌ Inactive'}\n"
            f"Authorized Devices: {len(self.authorized_devices)}/2",
            title="[bold blue]Port Manager Status[/bold blue]"
        ))
    
    def show_devices(self):
        """Show authorized and pending devices"""
        # Authorized devices table
        if self.authorized_devices:
            table = Table(title="Authorized Devices")
            table.add_column("IP Address", style="cyan")
            table.add_column("Device Name", style="green")
            table.add_column("Authorized At", style="yellow")
            table.add_column("Last Seen", style="blue")
            
            for ip, device in self.authorized_devices.items():
                table.add_row(
                    ip,
                    device['device_name'],
                    device['authorized_at'][:19],
                    device['last_seen'][:19]
                )
            console.print(table)
        else:
            console.print("[yellow]No authorized devices[/yellow]")
        
        # Pending requests table
        if self.pending_requests:
            console.print()
            table = Table(title="Pending Authentication Requests")
            table.add_column("ID", style="cyan")
            table.add_column("IP Address", style="red")
            table.add_column("Device Name", style="yellow")
            table.add_column("Timestamp", style="blue")
            
            for device_id, request in self.pending_requests.items():
                table.add_row(
                    device_id,
                    request['ip_address'],
                    request['device_name'],
                    request['timestamp'][:19]
                )
            console.print(table)
        else:
            console.print("[green]No pending requests[/green]")
    
    def cleanup_old_requests(self, max_age_hours=24):
        """Remove old pending requests"""
        current_time = time.time()
        expired_requests = []
        
        for device_id, request in self.pending_requests.items():
            request_time = datetime.fromisoformat(request['timestamp']).timestamp()
            if current_time - request_time > (max_age_hours * 3600):
                expired_requests.append(device_id)
        
        for device_id in expired_requests:
            del self.pending_requests[device_id]
        
        if expired_requests:
            console.print(f"[yellow]Cleaned up {len(expired_requests)} expired requests[/yellow]")
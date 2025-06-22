import os
import sys
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from InquirerPy import inquirer
from vive.modules.webserver.server import WebServer

console = Console()
VIVE_ENV_PATH = os.path.join(os.path.dirname(__file__), "vive", ".env")

class ViveServer:
    def __init__(self):
        self.web_server = None
        self.services = {
            "webserver": {"status": "stopped", "port": 5000, "instance": None}
        }
        self.logs = []
        self.config = {}
        self.running = False
        self.dashboard_active = False
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 50:  # Keep only last 50 logs
            self.logs.pop(0)

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
            
            self.web_server = WebServer(port=self.services["webserver"]["port"])
            self.web_server.start()
            self.services["webserver"]["status"] = "running"
            self.services["webserver"]["instance"] = self.web_server
            self.log(f"Web server started on port {self.services['webserver']['port']}")
        except Exception as e:
            self.log(f"Failed to start web server: {e}", "ERROR")
            self.services["webserver"]["status"] = "error"

    def stop_web_server(self):
        try:
            if self.web_server and self.services["webserver"]["status"] == "running":
                self.web_server.stop()
                self.services["webserver"]["status"] = "stopped"
                self.services["webserver"]["instance"] = None
                self.log("Web server stopped")
            else:
                self.log("Web server not running", "WARN")
        except Exception as e:
            self.log(f"Failed to stop web server: {e}", "ERROR")

    def get_system_info(self):
        import psutil
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": f"{cpu_percent:.1f}%",
                "memory": f"{memory.percent:.1f}%",
                "memory_used": f"{memory.used / (1024**3):.1f}GB",
                "memory_total": f"{memory.total / (1024**3):.1f}GB",
                "disk": f"{disk.percent:.1f}%",
                "disk_free": f"{disk.free / (1024**3):.1f}GB"
            }
        except:
            return {
                "cpu": "N/A", "memory": "N/A", "memory_used": "N/A",
                "memory_total": "N/A", "disk": "N/A", "disk_free": "N/A"
            }

    def create_dashboard(self):
        layout = Layout()
        
        # Split into header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into left and right
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left into services and system
        layout["left"].split_column(
            Layout(name="services", size=10),
            Layout(name="system")
        )
        
        # Split right into logs and config
        layout["right"].split_column(
            Layout(name="logs"),
            Layout(name="config", size=8)
        )

        # Header
        header_text = Text("ViVe Framework Server Dashboard", style="bold white on blue")
        header_text.pad_left = 2
        layout["header"].update(Panel(header_text, style="blue"))

        # Services status
        services_table = Table(title="Services Status", show_header=True, header_style="bold green")
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Status", style="magenta")
        services_table.add_column("Port", style="yellow")
        
        for service_name, service_info in self.services.items():
            status_style = "green" if service_info["status"] == "running" else "red"
            services_table.add_row(
                service_name.title(),
                f"[{status_style}]{service_info['status'].upper()}[/{status_style}]",
                str(service_info["port"])
            )
        
        layout["services"].update(Panel(services_table, title="Services", border_style="green"))

        # System info
        sys_info = self.get_system_info()
        system_table = Table(show_header=False)
        system_table.add_column("Metric", style="cyan")
        system_table.add_column("Value", style="green")
        
        system_table.add_row("CPU Usage", sys_info["cpu"])
        system_table.add_row("Memory", f"{sys_info['memory']} ({sys_info['memory_used']}/{sys_info['memory_total']})")
        system_table.add_row("Disk", f"{sys_info['disk']} (Free: {sys_info['disk_free']})")
        
        layout["system"].update(Panel(system_table, title="System Info", border_style="blue"))

        # Logs
        log_text = "\n".join(self.logs[-20:])  # Show last 20 logs
        layout["logs"].update(Panel(log_text, title="Logs", border_style="yellow"))

        # Config
        config_table = Table(show_header=True, header_style="bold magenta")
        config_table.add_column("Key", style="cyan")
        config_table.add_column("Value", style="white")
        
        for k, v in list(self.config.items())[:6]:  # Show first 6 config items
            # Hide sensitive values
            display_value = v if len(v) < 20 else v[:15] + "..."
            config_table.add_row(k, display_value)
        
        layout["config"].update(Panel(config_table, title="Configuration", border_style="magenta"))

        # Footer
        footer_text = "[q] Quit Dashboard | [m] Menu | [r] Restart Services | [s] Stop All"
        layout["footer"].update(Panel(footer_text, style="dim"))

        return layout

    def run_dashboard(self):
        self.dashboard_active = True
        self.log("Dashboard started - Press 'q' to exit")
        
        with Live(self.create_dashboard(), refresh_per_second=2, screen=True) as live:
            while self.dashboard_active:
                try:
                    # Non-blocking input check
                    import select
                    import sys
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key.lower() == 'q':
                            self.dashboard_active = False
                        elif key.lower() == 'm':
                            self.dashboard_active = False
                            return "menu"
                        elif key.lower() == 'r':
                            self.restart_all_services()
                        elif key.lower() == 's':
                            self.stop_all_services()
                    
                    live.update(self.create_dashboard())
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    self.dashboard_active = False
                except:
                    # Fallback for Windows
                    time.sleep(1)
                    live.update(self.create_dashboard())

    def restart_all_services(self):
        self.log("Restarting all services...")
        self.stop_all_services()
        time.sleep(1)
        self.start_all_services()

    def start_all_services(self):
        self.log("Starting all services...")
        self.start_web_server()

    def stop_all_services(self):
        self.log("Stopping all services...")
        self.stop_web_server()

    def show_menu(self):
        options = [
            "📊 Show Dashboard",
            "🔧 Show Config",
            "🔄 Reload Config",
            "🚀 Start All Services",
            "🛑 Stop All Services",
            "🌐 Start Web Server Only",
            "❌ Stop Web Server Only",
            "📝 View Logs",
            "🚪 Exit"
        ]
        choice = inquirer.select(
            message="ViVe Server Management - Select an option:",
            choices=options,
            default=options[0],
            pointer="👉"
        ).execute()
        return options.index(choice) + 1

    def show_config_menu(self):
        if not self.config:
            console.print("[yellow]No config loaded.[/yellow]")
            return
        
        table = Table(title="Current Configuration", show_header=True, header_style="bold green")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        for k, v in self.config.items():
            # Hide sensitive data
            display_value = v if "PASSWORD" not in k.upper() else "*" * len(v)
            table.add_row(k, display_value)
        
        console.print(table)

    def show_logs_menu(self):
        if not self.logs:
            console.print("[yellow]No logs available.[/yellow]")
            return
        
        console.print(Panel("\n".join(self.logs[-30:]), title="Recent Logs", border_style="yellow"))

    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        self.log("ViVe Server starting up...")
        self.config = self.load_config()
        self.running = True
        
        while self.running:
            self.clear_console()
            console.print(Panel(
                "ViVe Framework Server Manager\n"
                f"Services Running: {sum(1 for s in self.services.values() if s['status'] == 'running')}/{len(self.services)}\n"
                f"Config Items: {len(self.config)}",
                title="[bold blue]ViVe Server[/bold blue]",
                border_style="blue"
            ))
            
            choice = self.show_menu()
            
            if choice == 1:  # Dashboard
                result = self.run_dashboard()
                if result == "menu":
                    continue
            elif choice == 2:  # Show config
                self.show_config_menu()
                input("\nPress Enter to return to menu...")
            elif choice == 3:  # Reload config
                self.log("Reloading configuration...")
                self.config = self.load_config()
                input("\nPress Enter to return to menu...")
            elif choice == 4:  # Start all services
                self.start_all_services()
                input("\nPress Enter to return to menu...")
            elif choice == 5:  # Stop all services
                self.stop_all_services()
                input("\nPress Enter to return to menu...")
            elif choice == 6:  # Start web server
                self.start_web_server()
                input("\nPress Enter to return to menu...")
            elif choice == 7:  # Stop web server
                self.stop_web_server()
                input("\nPress Enter to return to menu...")
            elif choice == 8:  # View logs
                self.show_logs_menu()
                input("\nPress Enter to return to menu...")
            elif choice == 9:  # Exit
                self.log("Shutting down ViVe Server...")
                self.stop_all_services()
                self.running = False

if __name__ == "__main__":
    server = ViveServer()
    server.run()
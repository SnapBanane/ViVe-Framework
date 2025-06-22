import os
import sys
import threading
import time
from rich.console import Console
from rich.panel import Panel
from .app import run_server

console = Console()

class WebServer:
    def __init__(self, host='127.0.0.1', port=5000, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.server_thread = None
        self.running = False

    def start(self):
        """Start the web server in a separate thread"""
        if self.running:
            console.print("[yellow]Server is already running![/yellow]")
            return

        console.print(Panel(
            f"Starting ViVe Framework Web Server\n"
            f"Host: {self.host}\n"
            f"Port: {self.port}\n"
            f"Debug: {self.debug}",
            title="[bold blue]Web Server[/bold blue]"
        ))

        self.server_thread = threading.Thread(
            target=run_server,
            args=(self.host, self.port, self.debug),
            daemon=True
        )
        self.server_thread.start()
        self.running = True

        # Give server time to start
        time.sleep(1)
        console.print(f"[green]Server started at http://{self.host}:{self.port}[/green]")
        console.print("[cyan]Available endpoints:[/cyan]")
        console.print("  • GET  /api/health")
        console.print("  • POST /api/untis/login")
        console.print("  • GET  /api/untis/timetable")
        console.print("  • POST /api/upload")
        console.print("  • GET  /api/files")

    def stop(self):
        """Stop the web server"""
        if not self.running:
            console.print("[yellow]Server is not running![/yellow]")
            return

        self.running = False
        console.print("[red]Server stopped[/red]")

    def is_running(self):
        """Check if server is running"""
        return self.running

def main():
    """Main entry point for the web server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ViVe Framework Web Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    server = WebServer(host=args.host, port=args.port, debug=args.debug)
    server.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down server...[/yellow]")
        server.stop()

if __name__ == "__main__":
    main()
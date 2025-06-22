import os
import sys
import threading
import time
import logging
import io
import requests
from .app import app

# Completely suppress all Flask/Werkzeug output
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
logging.getLogger('flask').setLevel(logging.CRITICAL)

class WebServer:
    def __init__(self, host='0.0.0.0', port=2525):
        self.host = host
        self.port = port
        self.thread = None
        self.running = False
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def start(self):
        """Start the web server in a separate thread - SILENTLY"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.thread.start()
        
        # Wait for server to start
        time.sleep(2)
    
    def _run_server(self):
        """Run Flask app with ALL output suppressed"""
        try:
            # Redirect ALL output to null
            devnull = io.StringIO()
            sys.stdout = devnull
            sys.stderr = devnull
            
            app.run(
                host=self.host,
                port=self.port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
            
        except Exception as e:
            # Restore output only for critical errors
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            # Don't print anything - just fail silently
            self.running = False
        finally:
            # Always restore output when thread ends
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
    
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

        # Restore original stdout/stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def is_running(self):
        """Check if server is running"""
        return self.running and self.thread and self.thread.is_alive()

def run_server(host='0.0.0.0', port=2525):
    """Standalone function to run the server"""
    # Suppress ALL output
    import logging
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
    
    app.run(host=host, port=port, debug=False, threaded=True)
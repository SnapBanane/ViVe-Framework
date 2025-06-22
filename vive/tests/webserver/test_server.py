import requests
import time
from vive.modules.webserver.server import WebServer

def test_web_server():
    # Start server
    server = WebServer(debug=False)
    server.start()
    
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # Test printers endpoint
        response = requests.get(f"{base_url}/api/printers")
        print(f"Printers: {response.status_code} - {response.json()}")
        
        # Test Untis login
        response = requests.post(f"{base_url}/api/untis/login")
        print(f"Untis login: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            # Test timetable if login successful
            response = requests.get(f"{base_url}/api/untis/timetable")
            print(f"Timetable: {response.status_code} - {response.json()}")
        
    except Exception as e:
        print(f"Error testing server: {e}")
    
    finally:
        server.stop()

if __name__ == "__main__":
    test_web_server()
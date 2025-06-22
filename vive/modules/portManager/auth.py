from flask import request, jsonify, g
from functools import wraps
import json

def create_auth_middleware(port_manager):
    """Create authentication middleware for Flask"""
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Skip auth for localhost
            if client_ip in ['127.0.0.1', 'localhost', '::1']:
                return f(*args, **kwargs)
            
            # Check if device is authorized
            if port_manager.is_authorized(client_ip):
                return f(*args, **kwargs)
            
            # Add to pending requests
            user_agent = request.headers.get('User-Agent', 'Unknown')
            device_name = request.headers.get('X-Device-Name')
            
            port_manager.add_device_request(client_ip, user_agent, device_name)
            
            return jsonify({
                'status': 'unauthorized',
                'message': 'Device not authorized. Please wait for approval.',
                'ip': client_ip
            }), 401
        
        return decorated_function
    
    return require_auth
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import threading
import time
import os
from waitress import serve
from ..untis.client import UntisClient

# Create Flask app with template and static folders
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
CORS(app)

# Global client instance
untis_client = None

# Frontend routes
@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

# API routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api/untis/timetable', methods=['GET'])
def get_timetable():
    """Login to Untis and get timetable data"""
    global untis_client
    days_ahead = request.args.get('days', 1, type=int)
    
    try:
        # Always create a fresh client and login
        untis_client = UntisClient()
        untis_client.login()
        
        # Get timetable data
        timetable = untis_client.get_timetable(days_ahead=days_ahead)
        
        return jsonify({
            "status": "success", 
            "message": "Connected to Untis and retrieved timetable",
            "data": timetable
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file to the server"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        return jsonify({
            "status": "success", 
            "message": "File uploaded successfully",
            "filepath": file_path,
            "filename": file.filename
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """List uploaded files"""
    try:
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        if not os.path.exists(upload_dir):
            return jsonify({"status": "success", "data": []})
        
        files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
        return jsonify({"status": "success", "data": files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask server"""
    if debug:
        app.run(host=host, port=port, debug=True)
    else:
        serve(app, host=host, port=port)
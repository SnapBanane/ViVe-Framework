from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import os
import time
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import io
import threading

# --- App Setup ---
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
CORS(app)

# --- Directory Setup ---
INBOX_DIR = os.path.join(os.getcwd(), 'inbox')
OUTPUT_DIR = os.path.join(os.getcwd(), 'output')
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Document Processing Functions (Simplified & Self-Contained) ---

# Global list to store the points clicked by the user
manual_points = []

def mouse_callback(event, x, y, flags, param):
    """OpenCV mouse callback to capture the four corners of the document."""
    global manual_points
    
    image = param['image']
    window_name = param['window_name']

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(manual_points) < 4:
            # Add the clicked point
            manual_points.append((x, y))
            # Draw a circle to provide visual feedback
            cv2.circle(image, (x, y), 7, (0, 255, 0), -1)
            cv2.imshow(window_name, image)

def process_image_manually(image_path, output_pdf_path):
    """
    Opens a resized OpenCV window on the server's desktop for manual annotation,
    ensuring the window fits the screen, then processes the original high-res image.
    """
    global manual_points
    manual_points = []  # Reset points for each new image

    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")

        # --- RESIZING LOGIC FOR DISPLAY ---
        # Define max dimensions for the display window to ensure it fits on screen
        MAX_WIDTH = 1500
        MAX_HEIGHT = 850

        (h, w) = image.shape[:2]
        scale_factor = 1.0

        # Calculate the scaling factor if the image is larger than the max dimensions
        if w > MAX_WIDTH or h > MAX_HEIGHT:
            width_ratio = MAX_WIDTH / float(w)
            height_ratio = MAX_HEIGHT / float(h)
            scale_factor = min(width_ratio, height_ratio)
            
            new_width = int(w * scale_factor)
            new_height = int(h * scale_factor)
            
            display_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            display_image = image.copy()
        # --- END RESIZING LOGIC ---

        clone = display_image.copy()
        window_name = "Manual Selection: Click 4 corners, then press 'c' to crop or 'r' to reset."
        
        cv2.namedWindow(window_name)
        param = {'image': clone, 'window_name': window_name}
        cv2.setMouseCallback(window_name, mouse_callback, param)

        # Loop until user confirms selection
        while True:
            cv2.imshow(window_name, clone)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("r"):  # Reset points
                manual_points = []
                clone = display_image.copy()  # Reset with the resized display image
                cv2.imshow(window_name, clone)

            elif key == ord("c") and len(manual_points) == 4:  # Confirm points
                break
        
        cv2.destroyAllWindows()

        # Scale the clicked points back to the original image's dimensions
        original_points = np.array(manual_points, dtype="float32") / scale_factor

        # 1. Perspective Transform using scaled points on the ORIGINAL high-res image
        pts = original_points
        
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        processed_image = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        # 2. Enhance Image
        pil_img = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(pil_img)
        pil_img = enhancer.enhance(1.1)

        # 3. Save as PDF
        c = canvas.Canvas(output_pdf_path, pagesize=A4)
        img_width, img_height = pil_img.size
        page_width, page_height = A4
        scale = min(page_width / img_width, page_height / img_height)
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        x = (page_width - scaled_width) / 2
        y = (page_height - scaled_height) / 2
        
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        c.drawImage(ImageReader(img_buffer), x, y, scaled_width, scaled_height)
        c.save()

        # On success, delete the original image from the inbox
        os.remove(image_path)
        
        return {"success": True, "pdf_path": output_pdf_path}
        
    except Exception as e:
        cv2.destroyAllWindows() # Ensure window is closed on error
        app.logger.error(f"Error processing {image_path}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# --- Frontend Routes (Unchanged) ---
@app.route('/')
def index():
    """Serve the main frontend page"""
    if request.remote_addr != '127.0.0.1':
        return "Forbidden", 403
    return render_template('index.html')

@app.route('/mobile')
def mobile():
    """Serves the mobile-friendly interface."""
    return render_template('mobile.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

# --- API Routes (Updated and Added) ---
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handles file uploads, queues them for manual processing, and returns an immediate response."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        image_path = os.path.join(INBOX_DIR, filename)
        file.save(image_path)

        # Start manual processing in a background thread
        output_filename = os.path.splitext(filename)[0] + '.pdf'
        output_pdf_path = os.path.join(OUTPUT_DIR, output_filename)
        
        thread = threading.Thread(target=process_image_manually, args=(image_path, output_pdf_path))
        thread.start()

        # Return immediately
        return jsonify({
            "success": True, 
            "message": "File uploaded successfully. Manual processing started on the server."
        })

    return jsonify({"success": False, "error": "File upload failed"}), 500

# --- Error Handlers (Unchanged) ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

# --- Server Runner (Unchanged) ---
def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server"""
    if debug:
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve
        serve(app, host=host, port=port)
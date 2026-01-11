"""
Main Flask Application for Vision Guardian
FIXED: Secure file uploads, validation, size limits
"""
import base64
import cv2
import os
import tempfile
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS

from config import print_config, TEMPLATE_DIR, STATIC_DIR, SCREENSHOTS_DIR
from ai_integrator import AIModelIntegrator
from camera_manager import CameraManager
from integrity_handler import IntegrityHandler
from utils import  setup_logging,get_logger, success_response, error_response
from utils.file_utils import write_file, ensure_directory
# setup_logging
# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create Flask app
app = Flask(__name__, 
            template_folder=str(TEMPLATE_DIR),
            static_folder=str(STATIC_DIR))
CORS(app)

# Security Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 50000  # 50K characters
MAX_CODE_LENGTH = 100000  # 100K characters

ALLOWED_CODE_EXTENSIONS = {'.py', '.java', '.js', '.jsx', '.cpp', '.c', '.cs', '.txt'}
ALLOWED_TEXT_EXTENSIONS = {'.txt', '.md', '.doc', '.docx', '.pdf'}

# Print configuration
print_config()

# Initialize AI components
logger.info("🚀 Initializing Vision Guardian System...")
ai_integrator = AIModelIntegrator()
camera_manager = CameraManager(ai_integrator)
integrity_handler = IntegrityHandler(ai_integrator)

logger.info("✅ System initialized successfully!")

# ==================== SECURITY HELPERS ====================

def validate_file_size(file):
    """Validate file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
    return True, None

def validate_file_extension(filename, allowed_extensions):
    """Validate file extension"""
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    return True, None

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal"""
    # Remove any directory components
    filename = os.path.basename(filename)
    # Use werkzeug's secure_filename
    filename = secure_filename(filename)
    # Add timestamp to prevent collisions
    name, ext = os.path.splitext(filename)
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{ext}"

def validate_text_input(text, max_length):
    """Validate text input"""
    if not text or not isinstance(text, str):
        return False, "Text is required and must be a string"
    
    if len(text.strip()) == 0:
        return False, "Text cannot be empty"
    
    if len(text) > max_length:
        return False, f"Text too long. Maximum length: {max_length} characters"
    
    return True, None

def create_temp_file(content, extension):
    """Create a secure temporary file"""
    temp_dir = Path(tempfile.gettempdir()) / "vision_guardian"
    ensure_directory(temp_dir)
    
    # Create temp file
    fd, path = tempfile.mkstemp(suffix=extension, dir=str(temp_dir))
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
    except Exception as e:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)
        raise e

def cleanup_temp_file(filepath):
    """Safely cleanup temporary file"""
    try:
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {filepath}: {e}")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve main page"""
    logger.info("📄 Serving index.html")
    return render_template('index.html')

@app.route('/api/system_status', methods=['GET'])
def system_status():
    """Get system status"""
    try:
        from datetime import datetime
        
        status_data = {
            'camera_active': camera_manager.is_streaming if camera_manager else False,
            'ai_mode': 'REAL AI',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status_data,
            'message': 'System operational'
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'System status error: {str(e)}'
        }), 500

@app.route('/api/start_proctoring', methods=['POST'])
def start_proctoring():
    """Start proctoring session"""
    data = request.get_json() or {}
    camera_id = data.get('camera_id', 0)
    
    # Validate camera_id
    if not isinstance(camera_id, int) or camera_id < 0 or camera_id > 10:
        return jsonify(error_response('Invalid camera_id. Must be 0-10')), 400
    
    if camera_manager.start_camera(camera_id):
        return success_response(
            data={
                'camera_id': camera_id,
                'ai_mode': 'REAL_AI' if ai_integrator.ai_components['all_loaded'] else 'SIMULATION'
            },
            message='Proctoring started'
        )
    
    return error_response('Failed to start camera', 500)

@app.route('/api/stop_proctoring', methods=['POST'])
def stop_proctoring():
    """Stop proctoring session"""
    camera_manager.stop_camera()
    return success_response(message='Proctoring stopped')

@app.route('/api/proctoring_results')
def proctoring_results():
    """Get current proctoring results"""
    results = camera_manager.get_results()
    return success_response(data=results)

@app.route('/api/analyze_text', methods=['POST'])
def analyze_text():
    """Analyze text for AI generation - SECURE"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify(error_response('Text is required')), 400
    
    text = data['text']
    
    # Validate text input
    is_valid, error_msg = validate_text_input(text, MAX_TEXT_LENGTH)
    if not is_valid:
        return jsonify(error_response(error_msg)), 400
    
    try:
        results = integrity_handler.analyze_text_content(text)
        
        return success_response(
            data=results,
            message='Text analysis completed'
        )
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        return jsonify(error_response(f'Analysis failed: {str(e)}')), 500

@app.route('/api/check_code_plagiarism', methods=['POST'])
def check_code_plagiarism():
    """Check code plagiarism - SECURE"""
    data = request.get_json()
    if not data or 'code1' not in data or 'code2' not in data:
        return jsonify(error_response('Both code snippets are required')), 400
    
    code1 = data['code1']
    code2 = data['code2']
    language = data.get('language', 'python')
    
    # Validate code inputs
    is_valid1, error_msg1 = validate_text_input(code1, MAX_CODE_LENGTH)
    if not is_valid1:
        return jsonify(error_response(f'Code 1: {error_msg1}')), 400
    
    is_valid2, error_msg2 = validate_text_input(code2, MAX_CODE_LENGTH)
    if not is_valid2:
        return jsonify(error_response(f'Code 2: {error_msg2}')), 400
    
    # Validate language
    allowed_languages = ['python', 'java', 'javascript', 'cpp', 'c', 'cs']
    if language not in allowed_languages:
        return jsonify(error_response(f'Invalid language. Allowed: {", ".join(allowed_languages)}')), 400
    
    try:
        results = integrity_handler.check_code_plagiarism(code1, code2, language)
        
        return jsonify(success_response(
            message='Code plagiarism check completed',
            data=results
        ))
    except Exception as e:
        logger.error(f"Code plagiarism check error: {e}")
        return jsonify(error_response(f'Analysis failed: {str(e)}')), 500

@app.route('/api/compare_code_files', methods=['POST'])
def compare_code_files():
    """Compare two code files - SECURE"""
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify(error_response('Both files are required')), 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    # Validate filenames
    if not file1.filename or not file2.filename:
        return jsonify(error_response('Files must have filenames')), 400
    
    # Validate file sizes
    is_valid1, error_msg1 = validate_file_size(file1)
    if not is_valid1:
        return jsonify(error_response(f'File 1: {error_msg1}')), 400
    
    is_valid2, error_msg2 = validate_file_size(file2)
    if not is_valid2:
        return jsonify(error_response(f'File 2: {error_msg2}')), 400
    
    # Validate file extensions
    is_valid1, error_msg1 = validate_file_extension(file1.filename, ALLOWED_CODE_EXTENSIONS)
    if not is_valid1:
        return jsonify(error_response(f'File 1: {error_msg1}')), 400
    
    is_valid2, error_msg2 = validate_file_extension(file2.filename, ALLOWED_CODE_EXTENSIONS)
    if not is_valid2:
        return jsonify(error_response(f'File 2: {error_msg2}')), 400
    
    file1_path = None
    file2_path = None
    
    try:
        # Read file contents
        file1_content = file1.read().decode('utf-8')
        file2_content = file2.read().decode('utf-8')
        
        # Validate content length
        is_valid1, error_msg1 = validate_text_input(file1_content, MAX_CODE_LENGTH)
        if not is_valid1:
            return jsonify(error_response(f'File 1 content: {error_msg1}')), 400
        
        is_valid2, error_msg2 = validate_text_input(file2_content, MAX_CODE_LENGTH)
        if not is_valid2:
            return jsonify(error_response(f'File 2 content: {error_msg2}')), 400
        
        # Create secure temporary files
        ext1 = Path(file1.filename).suffix
        ext2 = Path(file2.filename).suffix
        
        file1_path = create_temp_file(file1_content, ext1)
        file2_path = create_temp_file(file2_content, ext2)
        
        # Compare files
        results = integrity_handler.compare_code_files(file1_path, file2_path)
        
        return jsonify(success_response(
            message='File comparison completed',
            data=results
        ))
        
    except UnicodeDecodeError:
        return jsonify(error_response('Files must be valid UTF-8 text')), 400
    except Exception as e:
        logger.error(f"File comparison error: {e}")
        return jsonify(error_response(f'Comparison failed: {str(e)}')), 500
    finally:
        # Always cleanup temp files
        cleanup_temp_file(file1_path)
        cleanup_temp_file(file2_path)

@app.route('/api/take_screenshot', methods=['POST'])
def take_screenshot():
    """Take screenshot"""
    screenshot = camera_manager.take_screenshot()
    if screenshot:
        filename, frame = screenshot
        
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        
        # Save to file
        filepath = SCREENSHOTS_DIR / safe_filename
        ensure_directory(SCREENSHOTS_DIR)
        cv2.imwrite(str(filepath), frame)
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify(success_response(
            message='Screenshot saved',
            data={
                'filename': safe_filename,
                'image': f'data:image/jpeg;base64,{img_base64}',
                'filepath': str(filepath)
            }
        ))
    
    return jsonify(error_response('No frame available')), 404

@app.route('/api/debug_detection')
def debug_detection():
    """Debug endpoint for detection"""
    frame = camera_manager.get_current_frame_bgr()
    if frame is not None:
        results = ai_integrator.process_frame(frame)
        
        # Convert to base64
        annotated_frame = results.get('annotated_frame', frame)
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify(success_response(data={
            'detections': results.get('detections', []),
            'detection_count': len(results.get('detections', [])),
            'persons': results.get('person_count', 0),
            'prohibited': results.get('prohibited_count', 0),
            'image': f'data:image/jpeg;base64,{img_base64}',
            'success': results.get('success', False)
        }))
    
    return jsonify(error_response('No frame available')), 404

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    def generate():
        while True:
            frame = camera_manager.get_current_frame()
            if frame is None:
                import time
                time.sleep(0.1)
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            import time
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    return jsonify(error_response('Endpoint not found', 'NOT_FOUND')), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error_response(f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB', 'FILE_TOO_LARGE')), 413

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify(error_response('Internal server error', 'INTERNAL_ERROR')), 500

# ==================== MAIN ENTRY ====================

if __name__ == '__main__':
    from config import FLASK_CONFIG
    
    # Set max content length
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    
    logger.info("=" * 60)
    logger.info(" VISION GUARDIAN BACKEND - SECURE VERSION")
    logger.info("=" * 60)
    logger.info(f" Templates: {TEMPLATE_DIR}")
    logger.info(f" Static: {STATIC_DIR}")
    logger.info(f" AI Status: {'REAL AI' if ai_integrator.ai_components['all_loaded'] else 'SIMULATION'}")
    logger.info(f" Max File Size: {MAX_FILE_SIZE / (1024*1024)}MB")
    logger.info(f" Starting server: http://{FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    logger.info("=" * 60)
    
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug'],
        threaded=FLASK_CONFIG['threaded'],
        use_reloader=False
    )
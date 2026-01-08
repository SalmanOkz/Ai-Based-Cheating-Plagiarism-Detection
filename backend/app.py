"""
Flask Backend for Vision Guardian - FIXED YOLO VERSION
"""
import os
import sys
import traceback

# Add parent directory to path to import your AI modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS
import cv2
import time
import threading
import json
import base64
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

print(f"🔧 Base directory: {BASE_DIR}")
print(f"📁 Template directory: {TEMPLATE_DIR}")
print(f"📁 Static directory: {STATIC_DIR}")

# Create Flask app with correct template and static folders
app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
CORS(app)

# Global variables for camera and AI
current_frame = None
current_frame_bgr = None
frame_lock = threading.Lock()
ai_results = {
    'fps': 0,
    'frame_count': 0,
    'violation_count': 0,
    'alert_level': 'NORMAL',
    'risk_score': 0,
    'is_cheating': False,
    'gaze_status': 'Looking Center',
    'person_count': 0,
    'prohibited_items': [],
    'processing_time': 0,
    'ai_mode': 'Checking...',
    'detections': []
}

# Global AI components
AI_COMPONENTS = {
    'guardian': None,
    'gaze_tracker': None,
    'object_detector': None,
    'yolo_model': None,
    'ai_available': False
}

def initialize_ai_components():
    """Initialize AI components in the main thread"""
    global AI_COMPONENTS
    
    print("\n" + "="*60)
    print("🤖 INITIALIZING AI COMPONENTS")
    print("="*60)
    
    try:
        # Try to import AI modules
        print("🔧 Importing AI modules...")
        from src.integrator import VisionGuardian
        from src.gaze_module import GazeTracker
        from src.object_module import ObjectDetector
        from ultralytics import YOLO
        
        print("✅ AI modules imported successfully")
        
        # Initialize YOLO model
        print("🔧 Loading YOLO model...")
        yolo_model_path = os.path.join(BASE_DIR, 'models', 'yolov8n.pt')
        if not os.path.exists(yolo_model_path):
            # Try to find the model
            model_paths = [
                'models/yolov8n.pt',
                '../models/yolov8n.pt',
                '../../models/yolov8n.pt',
                'yolov8n.pt'
            ]
            for path in model_paths:
                if os.path.exists(path):
                    yolo_model_path = path
                    break
        
        if os.path.exists(yolo_model_path):
            yolo_model = YOLO(yolo_model_path)
            print(f"✅ YOLO model loaded: {yolo_model_path}")
            AI_COMPONENTS['yolo_model'] = yolo_model
        else:
            print(f"❌ YOLO model not found at: {yolo_model_path}")
            print("⚠️ Please download yolov8n.pt to models/ directory")
            yolo_model = None
        
        # Initialize Vision Guardian
        print("🔧 Initializing Vision Guardian...")
        guardian = VisionGuardian({
            'enable_gaze': True,
            'enable_objects': True,
            'save_output': False,
            'max_students': 1
        })
        AI_COMPONENTS['guardian'] = guardian
        
        # Initialize Gaze Tracker
        print("🔧 Initializing Gaze Tracker...")
        try:
            gaze_tracker = GazeTracker()
            AI_COMPONENTS['gaze_tracker'] = gaze_tracker
            print("✅ Gaze Tracker initialized")
        except Exception as e:
            print(f"⚠️ Gaze Tracker failed: {e}")
        
        # Initialize Object Detector
        print("🔧 Initializing Object Detector...")
        try:
            object_detector = ObjectDetector()
            AI_COMPONENTS['object_detector'] = object_detector
            print("✅ Object Detector initialized")
        except Exception as e:
            print(f"⚠️ Object Detector failed: {e}")
        
        AI_COMPONENTS['ai_available'] = True
        ai_results['ai_mode'] = 'Real AI'
        print("✅✅✅ ALL AI COMPONENTS INITIALIZED SUCCESSFULLY!")
        print("="*60)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        traceback.print_exc()
        AI_COMPONENTS['ai_available'] = False
        ai_results['ai_mode'] = 'Simulation'
    except Exception as e:
        print(f"❌ Initialization Error: {e}")
        traceback.print_exc()
        AI_COMPONENTS['ai_available'] = False
        ai_results['ai_mode'] = 'Simulation'

# Initialize AI components
initialize_ai_components()

class CameraManager:
    """Manage camera operations with real YOLO detection"""
    def __init__(self):
        self.camera = None
        self.is_streaming = False
        self.processing_thread = None
        self.frame_count = 0
        self.start_time = time.time()
        self.violation_count = 0
        
        # Detection history
        self.detection_history = []
        self.max_history = 100
        
        print(f"📷 Camera Manager initialized | AI Available: {AI_COMPONENTS['ai_available']}")
    
    def start_camera(self, camera_id=0):
        """Start camera capture"""
        if self.camera is not None:
            self.camera.release()
        
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            print(f"❌ Failed to open camera {camera_id}")
            
            # Try different camera IDs
            for cam_id in [1, 2, 3]:
                self.camera = cv2.VideoCapture(cam_id)
                if self.camera.isOpened():
                    print(f"✅ Found camera at ID: {cam_id}")
                    break
            
            if not self.camera.isOpened():
                print("❌ No camera found!")
                return False
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Test camera
        ret, test_frame = self.camera.read()
        if not ret:
            print("❌ Camera test failed")
            self.camera.release()
            return False
        
        print(f"✅ Camera {camera_id} opened: {test_frame.shape[1]}x{test_frame.shape[0]}")
        
        self.is_streaming = True
        self.frame_count = 0
        self.start_time = time.time()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_frames)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        print(f"📷 Camera started successfully")
        return True
    
    def stop_camera(self):
        """Stop camera capture"""
        self.is_streaming = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        if self.camera:
            self.camera.release()
        self.camera = None
        print("📷 Camera stopped")
    
    def get_frame(self):
        """Get frame from camera"""
        if not self.camera or not self.camera.isOpened():
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        return frame
    
    def run_yolo_detection(self, frame):
        """Run YOLO object detection on frame"""
        if not AI_COMPONENTS['yolo_model']:
            return [], frame
        
        try:
            # Run YOLO inference
            results = AI_COMPONENTS['yolo_model'](
                frame,
                conf=0.5,
                iou=0.45,
                classes=[0, 67, 73],  # person, cell phone, book
                verbose=False
            )
            
            detections = []
            annotated_frame = frame.copy()
            
            if results and len(results) > 0:
                result = results[0]
                
                # Draw detections
                if hasattr(result, 'boxes') and result.boxes is not None:
                    for box in result.boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # Get class name
                        class_name = AI_COMPONENTS['yolo_model'].names[class_id]
                        
                        # Determine if it's a prohibited item
                        is_prohibited = class_id in [67, 73]  # cell phone, book
                        is_person = class_id == 0
                        
                        # Add to detections
                        detections.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'is_person': is_person,
                            'is_prohibited': is_prohibited
                        })
                        
                        # Draw bounding box
                        color = (0, 255, 0) if is_person else (0, 0, 255) if is_prohibited else (255, 0, 0)
                        thickness = 2 if is_person or is_prohibited else 1
                        
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
                        
                        # Draw label
                        label = f"{class_name} {confidence:.2f}"
                        cv2.putText(annotated_frame, label, (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            return detections, annotated_frame
            
        except Exception as e:
            print(f"❌ YOLO detection error: {e}")
            traceback.print_exc()
            return [], frame
    
    def run_gaze_detection(self, frame):
        """Run gaze detection on frame"""
        if not AI_COMPONENTS['gaze_tracker']:
            return {'status': 'Gaze tracker not available', 'level': 0}
        
        try:
            result = AI_COMPONENTS['gaze_tracker'].analyze_gaze(frame)
            return result
        except Exception as e:
            print(f"❌ Gaze detection error: {e}")
            return {'status': 'Gaze detection failed', 'level': 0}
    
    def analyze_with_vision_guardian(self, frame):
        """Analyze frame with Vision Guardian"""
        if not AI_COMPONENTS['guardian']:
            return None
        
        try:
            result = AI_COMPONENTS['guardian'].process_frame(frame)
            return result
        except Exception as e:
            print(f"❌ Vision Guardian error: {e}")
            return None
    
    def process_frames(self):
        """Process frames with AI"""
        print("🤖 Starting AI processing thread...")
        
        frame_skip = 2  # Process every 2nd frame to reduce load
        frame_counter = 0
        
        while self.is_streaming and self.camera and self.camera.isOpened():
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            frame_counter += 1
            if frame_counter % frame_skip != 0:
                time.sleep(0.01)
                continue
            
            self.frame_count += 1
            start_time = time.time()
            
            # Run YOLO detection
            detections, annotated_frame = self.run_yolo_detection(frame)
            
            # Count persons and prohibited items
            person_count = sum(1 for d in detections if d['is_person'])
            prohibited_items = [d for d in detections if d['is_prohibited']]
            
            # Run gaze detection
            gaze_result = self.run_gaze_detection(frame)
            
            # Run Vision Guardian analysis
            guardian_result = self.analyze_with_vision_guardian(frame)
            
            # Calculate risk score
            risk_score = 0
            
            # Risk from prohibited items
            if prohibited_items:
                risk_score += min(4, len(prohibited_items) * 2)
            
            # Risk from person count
            if person_count == 0:
                risk_score += 3  # No person
            elif person_count > 1:
                risk_score += 4  # Multiple persons
            
            # Risk from gaze
            if gaze_result and gaze_result.get('level', 0) >= 2:
                risk_score += 3
            elif gaze_result and gaze_result.get('level', 0) >= 1:
                risk_score += 1
            
            risk_score = min(10, risk_score)
            
            # Determine alert level
            is_cheating = False
            if risk_score >= 6:
                alert_level = 'CRITICAL'
                is_cheating = True
                self.violation_count += 1
            elif risk_score >= 3:
                alert_level = 'WARNING'
                is_cheating = False
            else:
                alert_level = 'NORMAL'
                is_cheating = False
            
            # Prepare prohibited items list
            prohibited_list = []
            for item in prohibited_items:
                prohibited_list.append({
                    'item': item['class_name'],
                    'confidence': round(item['confidence'], 2)
                })
            
            # Calculate FPS
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed if elapsed > 0 else 0
            
            # Store results
            results = {
                'fps': round(fps, 1),
                'frame_count': self.frame_count,
                'violation_count': self.violation_count,
                'alert_level': alert_level,
                'risk_score': risk_score,
                'is_cheating': is_cheating,
                'gaze_status': gaze_result.get('status', 'Unknown') if gaze_result else 'Unknown',
                'gaze_level': gaze_result.get('level', 0) if gaze_result else 0,
                'person_count': person_count,
                'prohibited_items': prohibited_list,
                'processing_time': round((time.time() - start_time) * 1000, 1),
                'ai_mode': ai_results['ai_mode'],
                'detections': detections,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store frame for streaming (use annotated frame)
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ret:
                with frame_lock:
                    global current_frame, current_frame_bgr
                    current_frame = buffer.tobytes()
                    current_frame_bgr = annotated_frame
            
            # Update global AI results
            # global ai_results
            ai_results.update(results)
            
            # Store in history
            self.detection_history.append(results)
            if len(self.detection_history) > self.max_history:
                self.detection_history.pop(0)
            
            # Print status every 50 frames
            if self.frame_count % 50 == 0:
                print(f"📊 Frame {self.frame_count} | FPS: {fps:.1f} | "
                      f"Persons: {person_count} | Prohibited: {len(prohibited_items)} | "
                      f"Risk: {risk_score}/10 | Alert: {alert_level}")
            
            # Limit processing to ~10 FPS
            time.sleep(0.1)
        
        print("🤖 AI processing thread stopped")

# Initialize camera manager
camera_manager = CameraManager()

# Flask Routes
@app.route('/')
def index():
    """Serve the main page"""
    print(f"📄 Serving index.html from {TEMPLATE_DIR}")
    return render_template('index.html')

@app.route('/api/start_proctoring', methods=['POST'])
def start_proctoring():
    """Start proctoring session"""
    if camera_manager.start_camera(0):
        return jsonify({
            'status': 'success', 
            'message': 'Proctoring started',
            'ai_mode': ai_results['ai_mode'],
            'camera_info': 'Camera initialized successfully'
        })
    return jsonify({'status': 'error', 'message': 'Failed to start camera'})

@app.route('/api/stop_proctoring', methods=['POST'])
def stop_proctoring():
    """Stop proctoring session"""
    camera_manager.stop_camera()
    return jsonify({'status': 'success', 'message': 'Proctoring stopped'})

@app.route('/api/get_results', methods=['GET'])
def get_results():
    """Get current AI results"""
    # Add camera status and additional info
    results = ai_results.copy()
    results['camera_active'] = camera_manager.is_streaming
    results['frames_processed'] = camera_manager.frame_count
    results['violations_detected'] = camera_manager.violation_count
    
    # Calculate uptime
    if camera_manager.start_time > 0:
        results['uptime'] = round(time.time() - camera_manager.start_time, 1)
    else:
        results['uptime'] = 0
    
    # Add detection debug info
    results['ai_debug'] = {
        'yolo_available': AI_COMPONENTS['yolo_model'] is not None,
        'gaze_available': AI_COMPONENTS['gaze_tracker'] is not None,
        'guardian_available': AI_COMPONENTS['guardian'] is not None,
        'total_detections': len(results.get('detections', []))
    }
    
    return jsonify(results)

@app.route('/api/take_screenshot', methods=['POST'])
def take_screenshot():
    """Take screenshot"""
    with frame_lock:
        if current_frame_bgr is not None:
            # Convert to base64
            ret, buffer = cv2.imencode('.jpg', current_frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ret:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.jpg"
                
                # Create screenshots directory if it doesn't exist
                screenshots_dir = os.path.join(BASE_DIR, 'screenshots')
                os.makedirs(screenshots_dir, exist_ok=True)
                filepath = os.path.join(screenshots_dir, filename)
                
                cv2.imwrite(filepath, current_frame_bgr)
                
                return jsonify({
                    'status': 'success',
                    'message': f'Screenshot saved as {filename}',
                    'filename': filename,
                    'image': f'data:image/jpeg;base64,{frame_base64}'
                })
    
    return jsonify({'status': 'error', 'message': 'No frame available'})

@app.route('/api/get_system_status', methods=['GET'])
def get_system_status():
    """Get system status"""
    status = {
        'ai_available': AI_COMPONENTS['ai_available'],
        'ai_mode': ai_results['ai_mode'],
        'camera_active': camera_manager.is_streaming,
        'camera_fps': ai_results.get('fps', 0),
        'frames_processed': camera_manager.frame_count,
        'violations_detected': camera_manager.violation_count,
        'uptime': round(time.time() - camera_manager.start_time, 1) if camera_manager.start_time > 0 else 0,
        'timestamp': datetime.now().isoformat(),
        'components': {
            'yolo': AI_COMPONENTS['yolo_model'] is not None,
            'gaze_tracker': AI_COMPONENTS['gaze_tracker'] is not None,
            'object_detector': AI_COMPONENTS['object_detector'] is not None,
            'vision_guardian': AI_COMPONENTS['guardian'] is not None
        }
    }
    return jsonify(status)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    def generate():
        while True:
            with frame_lock:
                if current_frame is None:
                    time.sleep(0.1)
                    continue
                
                frame = current_frame
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/test_ai', methods=['GET'])
def test_ai():
    """Test if AI modules are working"""
    # Test with a sample image
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = (100, 100, 100)  # Gray background
    
    # Add test text
    cv2.putText(test_frame, "AI Test Frame", (50, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Test YOLO
    yolo_working = False
    if AI_COMPONENTS['yolo_model']:
        try:
            results = AI_COMPONENTS['yolo_model'](test_frame, verbose=False)
            yolo_working = True
        except:
            yolo_working = False
    
    # Test gaze tracker
    gaze_working = False
    if AI_COMPONENTS['gaze_tracker']:
        try:
            result = AI_COMPONENTS['gaze_tracker'].analyze_gaze(test_frame)
            gaze_working = True
        except:
            gaze_working = False
    
    if AI_COMPONENTS['ai_available']:
        return jsonify({
            'status': 'success',
            'message': 'AI modules are available',
            'modules': {
                'yolo': yolo_working,
                'gaze_tracker': gaze_working,
                'object_detector': AI_COMPONENTS['object_detector'] is not None,
                'vision_guardian': AI_COMPONENTS['guardian'] is not None
            },
            'ai_mode': ai_results['ai_mode']
        })
    else:
        return jsonify({
            'status': 'warning',
            'message': 'Running in simulation mode',
            'modules': {},
            'ai_mode': 'Simulation'
        })

@app.route('/api/debug_detection', methods=['GET'])
def debug_detection():
    """Debug endpoint to check detection"""
    with frame_lock:
        if current_frame_bgr is not None:
            # Run detection on current frame
            detections, annotated = camera_manager.run_yolo_detection(current_frame_bgr)
            
            # Convert to base64
            ret, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if ret:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                return jsonify({
                    'status': 'success',
                    'detections': detections,
                    'detection_count': len(detections),
                    'persons': sum(1 for d in detections if d['is_person']),
                    'prohibited': sum(1 for d in detections if d['is_prohibited']),
                    'image': f'data:image/jpeg;base64,{frame_base64}'
                })
    
    return jsonify({
        'status': 'error',
        'message': 'No frame available for debugging'
    })

# Serve static files explicitly (for debugging)
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return app.send_static_file(filename)

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 VISION GUARDIAN - AI PROCTORING BACKEND")
    print("=" * 60)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Template Directory: {TEMPLATE_DIR}")
    print(f"Static Directory: {STATIC_DIR}")
    print(f"AI Status: {'✅ REAL AI' if AI_COMPONENTS['ai_available'] else '⚠️ SIMULATION MODE'}")
    
    if AI_COMPONENTS['ai_available']:
        print("📊 AI Components Status:")
        print(f"  • YOLO Model: {'✅ Loaded' if AI_COMPONENTS['yolo_model'] else '❌ Not available'}")
        print(f"  • Gaze Tracker: {'✅ Loaded' if AI_COMPONENTS['gaze_tracker'] else '❌ Not available'}")
        print(f"  • Object Detector: {'✅ Loaded' if AI_COMPONENTS['object_detector'] else '❌ Not available'}")
        print(f"  • Vision Guardian: {'✅ Loaded' if AI_COMPONENTS['guardian'] else '❌ Not available'}")
    
    print("\n🚀 Starting Flask server on http://127.0.0.1:5000")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
    
    # Create screenshots directory
    screenshots_dir = os.path.join(BASE_DIR, 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
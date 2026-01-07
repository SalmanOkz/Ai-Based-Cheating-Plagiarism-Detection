"""
Flask Backend for Vision Guardian Proctoring System
"""
from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS
import cv2
import time
import threading
import json
from pathlib import Path
import numpy as np

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
CORS(app)

# Global variables
current_frame = None
frame_lock = threading.Lock()
processing_stats = {
    'fps': 0,
    'frame_count': 0,
    'violation_count': 0,
    'alert_level': 'NORMAL',
    'risk_score': 0,
    'is_cheating': False,
    'gaze_status': 'Unknown',
    'person_count': 0,
    'prohibited_items': []
}

class ProctoringBackend:
    """Backend processing class"""
    def __init__(self):
        self.camera = None
        self.processing = False
        self.thread = None
        
    def start_processing(self, camera_index=0):
        """Start processing thread"""
        if self.processing:
            return
        
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            return False
        
        self.processing = True
        self.thread = threading.Thread(target=self.process_feed)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop_processing(self):
        """Stop processing thread"""
        self.processing = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.camera:
            self.camera.release()
        self.camera = None
    
    def process_feed(self):
        """Process video feed (simulated for now)"""
        frame_count = 0
        start_time = time.time()
        
        while self.processing and self.camera.isOpened():
            ret, frame = self.camera.read()
            if not ret:
                break
            
            # Process frame (simulated analysis)
            frame_count += 1
            
            # Simulate gaze detection
            gaze_statuses = [
                "Looking Center",
                "Looking Left",
                "Looking Right", 
                "Looking Down",
                "Looking Up"
            ]
            
            # Simulate object detection
            person_count = 1
            prohibited_items = []
            
            # Simulate violations
            is_cheating = frame_count % 100 < 5  # 5% chance of cheating
            alert_level = "CRITICAL" if is_cheating else "NORMAL"
            risk_score = 8 if is_cheating else 2
            
            # Update stats
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            global processing_stats
            processing_stats.update({
                'fps': round(fps, 1),
                'frame_count': frame_count,
                'violation_count': processing_stats['violation_count'] + (1 if is_cheating else 0),
                'alert_level': alert_level,
                'risk_score': risk_score,
                'is_cheating': is_cheating,
                'gaze_status': gaze_statuses[frame_count % len(gaze_statuses)],
                'person_count': person_count,
                'prohibited_items': ["cell phone"] if frame_count % 50 < 2 else []
            })
            
            # Encode frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame, 
                                      [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                with frame_lock:
                    global current_frame
                    current_frame = buffer.tobytes()
            
            # Limit to ~30 FPS
            time.sleep(0.03)
        
        self.processing = False

# Initialize backend
backend = ProctoringBackend()

def generate_frames():
    """Generate video frames for streaming"""
    while True:
        with frame_lock:
            if current_frame is None:
                time.sleep(0.1)
                continue
            
            frame = current_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_proctoring', methods=['POST'])
def start_proctoring():
    """Start proctoring session"""
    if backend.start_processing(0):
        return jsonify({'status': 'success', 'message': 'Proctoring started'})
    return jsonify({'status': 'error', 'message': 'Failed to start camera'})

@app.route('/stop_proctoring', methods=['POST'])
def stop_proctoring():
    """Stop proctoring session"""
    backend.stop_processing()
    return jsonify({'status': 'success', 'message': 'Proctoring stopped'})

@app.route('/get_stats', methods=['GET'])
def get_stats():
    """Get current statistics"""
    return jsonify(processing_stats)

@app.route('/take_screenshot', methods=['POST'])
def take_screenshot():
    """Take screenshot"""
    with frame_lock:
        if current_frame:
            # Save screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.jpg"
            filepath = Path("screenshots") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(current_frame)
            
            return jsonify({
                'status': 'success', 
                'message': f'Screenshot saved as {filename}',
                'filename': filename
            })
    
    return jsonify({'status': 'error', 'message': 'No frame available'})

@app.route('/get_violations', methods=['GET'])
def get_violations():
    """Get violation history"""
    # Simulated violation data
    violations = [
        {
            'id': 1,
            'timestamp': time.strftime("%H:%M:%S"),
            'type': 'Looking Down',
            'risk_score': 8,
            'duration': '3s'
        },
        {
            'id': 2,
            'timestamp': time.strftime("%H:%M:%S"),
            'type': 'Multiple Persons',
            'risk_score': 9,
            'duration': '5s'
        }
    ]
    return jsonify({'violations': violations})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
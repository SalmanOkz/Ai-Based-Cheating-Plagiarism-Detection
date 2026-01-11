"""
Camera Manager - Handles camera operations and frame processing
FIXED: Thread safety, frame counter, proper cleanup, race conditions
"""
import cv2
import time
import threading
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any
from queue import Queue, Empty

from config import AI_CONFIG
from utils.logging_utils import get_logger
from utils.risk_calculator import calculate_from_results

logger = get_logger(__name__)

class CameraManager:
    """Manages camera operations with AI processing - Thread Safe"""
    
    def __init__(self, ai_integrator):
        self.camera = None
        self.is_streaming = False
        self.processing_thread = None
        self.ai_integrator = ai_integrator
        
        # Thread-safe frame queue
        self.frame_queue = Queue(maxsize=2)  # Buffer only 2 frames
        
        # Statistics (thread-safe counters)
        self.frame_count = 0
        self.start_time = 0
        self.violation_count = 0
        self.fps = 0
        
        # Thread-safe locks
        self.camera_lock = threading.Lock()  # For camera access
        self.frame_lock = threading.Lock()    # For frame storage
        self.stats_lock = threading.Lock()    # For statistics
        
        # Frame storage
        self.current_frame = None
        self.current_frame_bgr = None
        
        # Results storage
        self.current_results = {
            'fps': 0,
            'frame_count': 0,
            'violation_count': 0,
            'alert_level': 'NORMAL',
            'risk_score': 0,
            'is_cheating': False,
            'gaze_status': 'Unknown',
            'person_count': 0,
            'prohibited_items': [],
            'processing_time': 0,
            'ai_mode': 'AI Ready',
            'detections': []
        }
        
        logger.info("📷 Camera Manager initialized (Thread-Safe)")
    
    def start_camera(self, camera_id: int = 0) -> bool:
        """Start camera capture - Thread Safe"""
        with self.camera_lock:
            # Stop existing camera
            if self.is_streaming:
                logger.warning("Camera already running, stopping first...")
                self._stop_camera_unsafe()

            # Try to open camera (Windows DirectShow backend)
            self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            
            if not self.camera.isOpened():
                # Try other camera IDs
                for cam_id in [1, 2, 3]:
                    self.camera = cv2.VideoCapture(cam_id)
                    if self.camera.isOpened():
                        camera_id = cam_id
                        break
            
            if not self.camera.isOpened():
                logger.error(f"❌ Failed to open any camera")
                return False
            
            # Set camera properties
           # Set camera properties (Windows optimization)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Warm up camera (flush initial frames)
            for _ in range(5):
                self.camera.read()# Minimize buffer lag
            
            # Test camera
            ret, test_frame = self.camera.read()
            if not ret:
                logger.error("❌ Camera test failed")
                self.camera.release()
                self.camera = None
                return False
            
            logger.info(f"✅ Camera {camera_id} opened: {test_frame.shape[1]}x{test_frame.shape[0]}")
            
            # Reset statistics
            with self.stats_lock:
                self.frame_count = 0
                self.violation_count = 0
                self.start_time = time.time()
            
            # Clear frame queue
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Empty:
                    break
            
            # Start streaming
            self.is_streaming = True
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._process_frames,
                name="CameraProcessingThread",
                daemon=True
            )
            self.processing_thread.start()
            
            logger.info("📷 Camera started successfully")
            return True
    
    def stop_camera(self):
        """Stop camera capture - Thread Safe"""
        with self.camera_lock:
            self._stop_camera_unsafe()
    
    def _stop_camera_unsafe(self):
        """Internal stop (must be called with camera_lock held)"""
        self.is_streaming = False
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Waiting for processing thread to stop...")
            self.processing_thread.join(timeout=3.0)
            if self.processing_thread.is_alive():
                logger.warning("Processing thread did not stop gracefully")
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("📷 Camera stopped")
    
    def _process_frames(self):
        """Process frames with AI - Thread Safe"""
        logger.info("🤖 Starting frame processing thread...")
        
        frame_skip = AI_CONFIG['frame_skip']
        local_frame_counter = 0  # Local counter for frame skipping
        
        while self.is_streaming:
            try:
                # Read frame (thread-safe)
                with self.camera_lock:
                    if not self.camera or not self.camera.isOpened():
                        break
                    ret, frame = self.camera.read()
                
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Frame skipping logic
                local_frame_counter += 1
                if local_frame_counter % frame_skip != 0:
                    time.sleep(0.01)
                    continue
                
                # Increment global frame count
                with self.stats_lock:
                    self.frame_count += 1
                    current_frame_count = self.frame_count
                
                process_start = time.time()
                
                # Process frame with AI
                results = self.ai_integrator.process_frame(frame)
                
                if results.get('success', False):
                    # Calculate risk score using unified calculator
                    risk_data = calculate_from_results(results, max_students=AI_CONFIG['max_students'])
                    risk_score = risk_data['risk_score']
                    alert_level = risk_data['alert_level']
                    is_cheating = risk_data['is_cheating']
                    
                    # Update violation count
                    if is_cheating:
                        with self.stats_lock:
                            self.violation_count += 1
                    
                    # Calculate FPS
                    with self.stats_lock:
                        elapsed = time.time() - self.start_time
                        fps = self.frame_count / elapsed if elapsed > 0 else 0
                    
                    # Prepare prohibited items list
                    prohibited_items = []
                    for detection in results.get('detections', []):
                        if detection.get('is_prohibited', False):
                            prohibited_items.append({
                                'item': detection.get('class_name', 'unknown'),
                                'confidence': round(detection.get('confidence', 0), 2)
                            })
                    
                    # Get gaze status safely
                    gaze_analysis = results.get('gaze_analysis', {})
                    gaze_status = gaze_analysis.get('status', 'Unknown') if gaze_analysis else 'Unknown'
                    
                    # Update current results (no lock needed, only written by this thread)
                    self.current_results.update({
                        'fps': round(fps, 1),
                        'frame_count': current_frame_count,
                        'violation_count': self.violation_count,
                        'alert_level': alert_level,
                        'risk_score': risk_score,
                        'is_cheating': is_cheating,
                        'gaze_status': gaze_status,
                        'person_count': results.get('person_count', 0),
                        'prohibited_items': prohibited_items,
                        'processing_time': round((time.time() - process_start) * 1000, 1),
                        'detections': results.get('detections', []),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Store frame for streaming (thread-safe)
                    if 'annotated_frame' in results:
                        ret, buffer = cv2.imencode(
                            '.jpg', 
                            results['annotated_frame'], 
                            [cv2.IMWRITE_JPEG_QUALITY, 75]
                        )
                        if ret:
                            with self.frame_lock:
                                self.current_frame = buffer.tobytes()
                                self.current_frame_bgr = results['annotated_frame'].copy()
                
                # Log periodically
                if current_frame_count % 50 == 0:
                    logger.info(
                        f"📊 Frame {current_frame_count} | "
                        f"FPS: {self.current_results['fps']} | "
                        f"Persons: {self.current_results['person_count']} | "
                        f"Risk: {self.current_results['risk_score']}/10"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Frame processing error: {e}")
            
            # Maintain target FPS
            time.sleep(1 / AI_CONFIG['target_fps'])
        
        logger.info("🤖 Frame processing thread stopped")
    
    def _calculate_risk_score(self, results: Dict) -> int:
        """Calculate risk score from detection results"""
        risk_score = 0
        
        # Risk from prohibited items
        prohibited_count = results.get('prohibited_count', 0)
        risk_score += min(4, prohibited_count * 2)
        
        # Risk from person count
        person_count = results.get('person_count', 0)
        if person_count == 0:
            risk_score += 3  # No person
        elif person_count > 1:
            risk_score += 4  # Multiple persons
        
        # Risk from gaze
        gaze_analysis = results.get('gaze_analysis', {})
        if gaze_analysis:
            gaze_level = gaze_analysis.get('level', 0)
            if gaze_level >= 2:
                risk_score += 3
            elif gaze_level >= 1:
                risk_score += 1
        
        return min(10, risk_score)
    
    def _determine_alert(self, risk_score: int) -> Tuple[str, bool]:
        """Determine alert level based on risk score"""
        if risk_score >= 6:
            return 'CRITICAL', True
        elif risk_score >= 3:
            return 'WARNING', False
        else:
            return 'NORMAL', False
    
    def get_current_frame(self) -> Optional[bytes]:
        """Get current frame as JPEG bytes - Thread Safe"""
        with self.frame_lock:
            return self.current_frame
    
    def get_current_frame_bgr(self) -> Optional[np.ndarray]:
        """Get current frame as BGR array - Thread Safe"""
        with self.frame_lock:
            if self.current_frame_bgr is not None:
                return self.current_frame_bgr.copy()
            return None
    
    def get_results(self) -> Dict:
        """Get current processing results - Thread Safe"""
        results = self.current_results.copy()
        
        with self.stats_lock:
            uptime = round(time.time() - self.start_time, 1) if self.start_time > 0 else 0
        
        results.update({
            'camera_active': self.is_streaming,
            'frames_processed': self.frame_count,
            'violations_detected': self.violation_count,
            'uptime': uptime
        })
        return results
    
    def take_screenshot(self) -> Optional[Tuple[str, np.ndarray]]:
        """Take screenshot of current frame - Thread Safe"""
        with self.frame_lock:
            if self.current_frame_bgr is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.jpg"
                return filename, self.current_frame_bgr.copy()
        return None
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.stop_camera()
        except:
            pass
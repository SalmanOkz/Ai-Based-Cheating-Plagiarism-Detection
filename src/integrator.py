"""
Vision Guardian Integrator - FIXED
"""
import cv2
import time
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Try importing components
try:
    from src.gaze_module import GazeTracker
    GAZE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Gaze tracker import failed: {e}")
    GAZE_AVAILABLE = False
    GazeTracker = None

try:
    from src.object_module import ObjectDetector
    OBJECT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Object detector import failed: {e}")
    OBJECT_AVAILABLE = False
    ObjectDetector = None


class VisionGuardian:
    """Main proctoring system - FIXED"""
    
    def __init__(self, config: Dict = None):
        """Initialize with configuration"""
        # Default configuration
        self.config = {
            'enable_gaze': True,
            'enable_objects': True,
            'save_output': True,
            'output_dir': 'proctoring_results',
            'gaze_confidence': 0.5,
            'object_confidence': 0.5,
            'max_persons': 1,
            'violation_cooldown': 5
        }
        
        if config:
            self.config.update(config)
        
        # Override based on availability
        if not GAZE_AVAILABLE:
            self.config['enable_gaze'] = False
            print("⚠️ Gaze tracking disabled (module not available)")
        
        if not OBJECT_AVAILABLE:
            self.config['enable_objects'] = False
            print("⚠️ Object detection disabled (module not available)")
        
        # Initialize components
        self.initialize_components()
        
        # State tracking
        self.frame_count = 0
        self.violation_count = 0
        self.last_violation_time = 0
        self.start_time = time.time()
        
        # Create output directory
        if self.config['save_output']:
            Path(self.config['output_dir']).mkdir(parents=True, exist_ok=True)
            print(f"📁 Output directory: {self.config['output_dir']}")
    
    def initialize_components(self):
        """Initialize components based on configuration"""
        self.gaze_tracker = None
        self.object_detector = None
        
        # Initialize gaze tracker if enabled
        if self.config['enable_gaze'] and GAZE_AVAILABLE:
            try:
                self.gaze_tracker = GazeTracker()
                print("✅ Gaze tracker initialized")
            except Exception as e:
                print(f"❌ Gaze tracker failed: {e}")
                self.gaze_tracker = None
        
        # Initialize object detector if enabled
        if self.config['enable_objects'] and OBJECT_AVAILABLE:
            try:
                self.object_detector = ObjectDetector()
                print("✅ Object detector initialized")
            except Exception as e:
                print(f"❌ Object detector failed: {e}")
                self.object_detector = None
        
        # Warn if no components available
        if self.gaze_tracker is None and self.object_detector is None:
            print("⚠️ WARNING: No detection components available!")
    
    def process_frame(self, frame, frame_id: int = None):
        """Process single frame - FIXED"""
        self.frame_count += 1
        if frame_id is None:
            frame_id = self.frame_count
        
        # Initialize results
        results = {
            'frame_id': frame_id,
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat(),
            'gaze_analysis': None,
            'object_analysis': None,
            'violations': [],
            'risk_score': 0,
            'is_cheating': False,
            'alert_level': 'NORMAL',
            'processing_time': 0
        }
        
        start_process = time.time()
        
        # Gaze analysis
        if self.gaze_tracker:
            try:
                gaze_result = self.gaze_tracker.analyze_gaze(frame)
                results['gaze_analysis'] = gaze_result
                
                # Add violations if any
                if gaze_result.get('level', 0) > 0:
                    results['violations'].append(f"GAZE: {gaze_result.get('status', 'Unknown')}")
            except Exception as e:
                results['violations'].append(f"GAZE_ERROR: {str(e)}")
                print(f"⚠️ Gaze analysis error: {e}")
        
        # Object analysis
        if self.object_detector:
            try:
                object_result = self.object_detector.analyze_proctoring(frame)
                results['object_analysis'] = object_result
                
                # Add violations
                for violation in object_result.get('violations', []):
                    results['violations'].append(violation)
            except Exception as e:
                results['violations'].append(f"OBJECT_ERROR: {str(e)}")
                print(f"⚠️ Object analysis error: {e}")
        
        # Calculate risk score
        results['risk_score'] = self.calculate_risk_score(results)
        
        # Determine alert level
        results['alert_level'] = self.determine_alert_level(results)
        results['is_cheating'] = results['alert_level'] in ['WARNING', 'CRITICAL']
        
        # Save violation if needed
        if results['is_cheating'] and self.config['save_output']:
            self.save_violation(frame, results)
        
        # Calculate processing time
        results['processing_time'] = round((time.time() - start_process) * 1000, 2)
        
        return results
    
    def calculate_risk_score(self, results: Dict) -> int:
        """Calculate risk score"""
        risk = 0
        
        # Gaze risk
        gaze = results.get('gaze_analysis', {})
        gaze_level = gaze.get('level', 0)
        if gaze_level == 2:
            risk += 4
        elif gaze_level == 1:
            risk += 2
        
        # Object risk
        obj = results.get('object_analysis', {})
        obj_level = obj.get('level', 0)
        if obj_level == 2:
            risk += 4
        elif obj_level == 1:
            risk += 2
        
        # Presence risk
        person_count = obj.get('person_count', 0)
        if person_count == 0 or person_count > self.config.get('max_persons', 1):
            risk += 3
        
        # Violation penalty
        violation_count = len(results.get('violations', []))
        risk += min(2, violation_count)
        
        return min(10, risk)
    
    def determine_alert_level(self, results: Dict) -> str:
        """Determine alert level"""
        risk_score = results.get('risk_score', 0)
        violations = results.get('violations', [])
        
        # Check for critical violations
        critical_keywords = ['PROHIBITED', 'NO_PERSON', 'MULTIPLE_PERSONS']
        has_critical = any(any(keyword in v for keyword in critical_keywords) 
                          for v in violations)
        
        if has_critical or risk_score >= 6:
            return 'CRITICAL'
        elif risk_score >= 3 or violations:
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def save_violation(self, frame: np.ndarray, results: Dict):
        """Save violation data"""
        # Cooldown check
        current_time = time.time()
        if current_time - self.last_violation_time < self.config.get('violation_cooldown', 5):
            return
        
        self.last_violation_time = current_time
        self.violation_count += 1
        
        try:
            # Create directories
            output_dir = Path(self.config['output_dir'])
            violations_dir = output_dir / 'violations'
            violations_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violation_{timestamp}_f{results['frame_id']:06d}.jpg"
            
            # Save annotated frame
            annotated = self.annotate_frame(frame, results)
            image_path = violations_dir / filename
            cv2.imwrite(str(image_path), annotated)
            
            # Save metadata
            metadata = results.copy()
            metadata['saved_image'] = str(image_path)
            metadata_path = violations_dir / f"{filename}.json"
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            print(f"⚠️ Violation saved: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save violation: {e}")
    
    def annotate_frame(self, frame: np.ndarray, results: Dict) -> np.ndarray:
        """Annotate frame with results"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Colors for alert levels
        colors = {
            'NORMAL': (0, 255, 0),    # Green
            'WARNING': (0, 255, 255), # Yellow
            'CRITICAL': (0, 0, 255)   # Red
        }
        
        alert_level = results.get('alert_level', 'NORMAL')
        color = colors.get(alert_level, (255, 255, 255))
        
        # Top banner
        banner_height = 80
        cv2.rectangle(annotated, (0, 0), (w, banner_height), color, -1)
        
        # Title
        title = f"Vision Guardian - {alert_level}"
        cv2.putText(annotated, title, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Info lines
        info_lines = [
            f"Frame: {results.get('frame_id', 0)} | Risk: {results.get('risk_score', 0)}/10",
            f"Time: {results.get('timestamp', 0):.1f}s | Processing: {results.get('processing_time', 0)}ms"
        ]
        
        for i, line in enumerate(info_lines):
            cv2.putText(annotated, line, (10, 55 + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Gaze info
        gaze = results.get('gaze_analysis', {})
        if gaze:
            gaze_text = f"Gaze: {gaze.get('status', 'N/A')}"
            cv2.putText(annotated, gaze_text, (10, h - 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Object info
        obj = results.get('object_analysis', {})
        if obj:
            obj_text = f"Persons: {obj.get('person_count', 0)}"
            cv2.putText(annotated, obj_text, (10, h - 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            items = obj.get('prohibited_items', [])
            if items:
                items_text = f"Items: {len(items)}"
                cv2.putText(annotated, items_text, (10, h - 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Violations
        violations = results.get('violations', [])
        if violations:
            cv2.putText(annotated, "Violations:", (w - 200, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            for i, violation in enumerate(violations[:3]):
                cv2.putText(annotated, f"• {violation}", (w - 200, 55 + i * 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        return annotated
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'frames_processed': self.frame_count,
            'violations_detected': self.violation_count,
            'violation_rate': self.violation_count / max(self.frame_count, 1),
            'fps': round(fps, 1),
            'elapsed_time': round(elapsed, 1),
            'components_active': {
                'gaze': self.gaze_tracker is not None,
                'objects': self.object_detector is not None
            }
        }
"""
Enhanced Object Detector with YOLOv8 for Proctoring
FIXED: Memory leaks, bounded collections, cleanup
"""
import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import deque
import time

@dataclass
class Detection:
    """Data class for detection results"""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    is_person: bool = False
    is_prohibited: bool = False
    track_id: Optional[int] = None
    timestamp: float = 0.0

@dataclass
class Student:
    """Data class for tracked student - FIXED: Bounded history"""
    track_id: int
    bbox: List[float]
    confidence: float
    last_seen: float
    position_history: deque = field(default_factory=lambda: deque(maxlen=20))  # FIXED: maxlen
    activity_score: float = 0.0
    suspicious_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure bounded collections"""
        if not isinstance(self.position_history, deque):
            self.position_history = deque(self.position_history, maxlen=20)
        # FIXED: Limit suspicious actions
        if len(self.suspicious_actions) > 50:
            self.suspicious_actions = self.suspicious_actions[-50:]

class ObjectDetector:
    """Enhanced object detector - FIXED: Memory safe"""
    
    # Constants
    MAX_TRACKED_STUDENTS = 10  # FIXED: Limit tracked students
    MAX_ACTIVITY_HISTORY = 100  # FIXED: Limit activity history
    MAX_SUSPICIOUS_ACTIONS = 50  # FIXED: Limit per student
    TRACK_TIMEOUT = 5.0  # Seconds before removing old tracks
    
    # Prohibited classes (COCO dataset)
    PROHIBITED_CLASSES = {
        67: 'cell phone',
        73: 'book',
        61: 'dining table',
        39: 'bottle',
        41: 'cup',
        76: 'scissors',
        63: 'laptop',
        62: 'toilet',
        77: 'teddy bear',
        27: 'backpack',
        28: 'umbrella'
    }
    
    # Suspicious activities
    SUSPICIOUS_ACTIONS = {
        'MULTIPLE_PERSONS': "Multiple students detected",
        'NO_PERSON': "No student in frame",
        'PHONE_DETECTED': "Mobile phone detected",
        'BOOK_DETECTED': "Book or notes detected",
        'UNUSUAL_OBJECT': "Suspicious object detected",
        'PERSON_LEAVING': "Student left the frame",
        'PERSON_ENTERING': "New person entered",
        'CLOSE_PROXIMITY': "Persons too close (possible collaboration)"
    }
    
    def __init__(self, model_path='models/yolov8n.pt', device='cpu'):
        """Initialize enhanced detector"""
        print(f"🔧 Loading YOLO model: {model_path}")
        
        try:
            self.model = YOLO(model_path)
            self.device = device
            self.class_names = self.model.names
            
            # Detection parameters
            self.conf_threshold = 0.5
            self.iou_threshold = 0.45
            
            # FIXED: Bounded tracking and activity monitoring
            self.next_track_id = 0
            self.tracked_students = {}  # track_id -> Student
            self.activity_history = deque(maxlen=self.MAX_ACTIVITY_HISTORY)
            self.violation_count = 0
            
            # Alert thresholds
            self.max_students = 1
            self.max_absent_time = 5.0
            self.proximity_threshold = 100
            
            # Cleanup tracking
            self.last_cleanup_time = time.time()
            self.cleanup_interval = 10.0  # Cleanup every 10 seconds
            
            print(f"✅ YOLO loaded: {len(self.class_names)} classes")
            
        except Exception as e:
            print(f"❌ Failed to load YOLO: {e}")
            self.model = None
    
    def detect(self, frame, conf=None, classes=None):
        """Detect objects in frame with tracking - FIXED: Memory safe"""
        if self.model is None:
            return [], frame
        
        # Auto cleanup periodically
        current_time = time.time()
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            self._cleanup_old_tracks(current_time)
            self.last_cleanup_time = current_time
        
        # Run inference with tracking
        results = self.model.track(
            frame,
            conf=conf or self.conf_threshold,
            iou=self.iou_threshold,
            classes=classes or [0] + list(self.PROHIBITED_CLASSES.keys()),
            device=self.device,
            persist=True,
            verbose=False
        )
        
        detections = []
        
        for result in results:
            if result.boxes is None:
                continue
            
            # Get tracking IDs if available
            track_ids = []
            if result.boxes.id is not None:
                track_ids = result.boxes.id.cpu().numpy().astype(int)
            
            for idx, box in enumerate(result.boxes):
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()
                
                # Get track ID
                track_id = None
                if idx < len(track_ids):
                    track_id = int(track_ids[idx])
                    if track_id not in self.tracked_students and cls_id == 0:
                        # New student detected
                        self._register_student(track_id, bbox, conf, current_time)
                
                detection = Detection(
                    class_id=cls_id,
                    class_name=self.class_names[cls_id],
                    confidence=conf,
                    bbox=bbox.tolist(),
                    is_person=cls_id == 0,
                    is_prohibited=cls_id in self.PROHIBITED_CLASSES,
                    track_id=track_id,
                    timestamp=current_time
                )
                detections.append(detection)
                
                # Update tracked student
                if track_id is not None and cls_id == 0:
                    self._update_student(track_id, bbox, conf, current_time)
        
        # Clean up old tracks
        self._cleanup_tracks(current_time)
        
        # Get annotated frame
        annotated = results[0].plot() if results else frame.copy()
        
        return detections, annotated
    
    def _register_student(self, track_id, bbox, confidence, timestamp):
        """Register a new student - FIXED: Memory safe"""
        # FIXED: Limit number of tracked students
        if len(self.tracked_students) >= self.MAX_TRACKED_STUDENTS:
            # Remove oldest student
            oldest_id = min(self.tracked_students.keys(), 
                          key=lambda k: self.tracked_students[k].last_seen)
            del self.tracked_students[oldest_id]
            print(f"⚠️ Max students reached, removed oldest: {oldest_id}")
        
        student = Student(
            track_id=track_id,
            bbox=bbox.tolist(),
            confidence=confidence,
            last_seen=timestamp,
            position_history=deque(maxlen=20)
        )
        self.tracked_students[track_id] = student
        
        print(f"🎓 New student detected (ID: {track_id})")
        self._log_activity(f"Student {track_id} entered the frame")
    
    def _update_student(self, track_id, bbox, confidence, timestamp):
        """Update tracked student information"""
        if track_id not in self.tracked_students:
            return
        
        student = self.tracked_students[track_id]
        student.bbox = bbox.tolist()
        student.confidence = confidence
        student.last_seen = timestamp
        
        # Add to position history (deque auto-discards oldest)
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        student.position_history.append((center_x, center_y, timestamp))
        
        # FIXED: Limit suspicious actions
        if len(student.suspicious_actions) > self.MAX_SUSPICIOUS_ACTIONS:
            student.suspicious_actions = student.suspicious_actions[-self.MAX_SUSPICIOUS_ACTIONS:]
    
    def _cleanup_tracks(self, current_time):
        """Remove inactive tracks"""
        tracks_to_remove = []
        for track_id, student in self.tracked_students.items():
            if current_time - student.last_seen > 2.0:
                tracks_to_remove.append(track_id)
                print(f"🎓 Student {track_id} left the frame")
                self._log_activity(f"Student {track_id} left the frame")
        
        for track_id in tracks_to_remove:
            del self.tracked_students[track_id]
    
    def _cleanup_old_tracks(self, current_time):
        """Periodic cleanup of very old tracks - FIXED"""
        tracks_to_remove = []
        for track_id, student in self.tracked_students.items():
            if current_time - student.last_seen > self.TRACK_TIMEOUT:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracked_students[track_id]
        
        if tracks_to_remove:
            print(f"🧹 Cleaned up {len(tracks_to_remove)} old tracks")
    
    def _log_activity(self, activity):
        """Log suspicious activity - FIXED: Memory safe"""
        log_entry = {
            'timestamp': time.time(),
            'activity': activity,
            'tracked_students': len(self.tracked_students)
        }
        # deque auto-discards oldest when maxlen reached
        self.activity_history.append(log_entry)
    
    def analyze_student_activity(self, frame):
        """Comprehensive analysis - FIXED: Memory safe"""
        detections, annotated = self.detect(frame)
        
        # Extract persons and prohibited items
        persons = [d for d in detections if d.is_person]
        prohibited_items = [d for d in detections if d.is_prohibited and d.confidence > 0.5]
        
        # Analyze suspicious activities
        suspicious_activities = []
        risk_factors = []
        detailed_analysis = {
            'student_count': len(persons),
            'tracked_students': len(self.tracked_students),
            'prohibited_items_count': len(prohibited_items),
            'student_positions': [],
            'activity_timeline': list(self.activity_history)[-5:],  # Last 5 only
            'proximity_warnings': []
        }
        
        # Check for multiple students
        if len(persons) > self.max_students:
            activity = self.SUSPICIOUS_ACTIONS['MULTIPLE_PERSONS']
            suspicious_activities.append(activity)
            risk_factors.append(('multiple_persons', 3.0))
            detailed_analysis['multiple_students'] = {
                'count': len(persons),
                'allowed': self.max_students,
                'violation': True
            }
        
        # Check for no student
        if len(persons) == 0:
            activity = self.SUSPICIOUS_ACTIONS['NO_PERSON']
            suspicious_activities.append(activity)
            risk_factors.append(('no_person', 4.0))
            detailed_analysis['absent_student'] = True
        
        # Analyze prohibited items
        if prohibited_items:
            for item in prohibited_items:
                if item.class_name == 'cell phone':
                    activity = self.SUSPICIOUS_ACTIONS['PHONE_DETECTED']
                elif item.class_name == 'book':
                    activity = self.SUSPICIOUS_ACTIONS['BOOK_DETECTED']
                else:
                    activity = self.SUSPICIOUS_ACTIONS['UNUSUAL_OBJECT'] + f": {item.class_name}"
                
                suspicious_activities.append(activity)
                risk_factors.append((f'prohibited_{item.class_name}', 2.5))
            
            detailed_analysis['prohibited_items'] = [
                {'item': item.class_name, 'confidence': item.confidence}
                for item in prohibited_items
            ]
        
        # Store student info (FIXED: Limited)
        for track_id, student in list(self.tracked_students.items())[:10]:  # Max 10
            detailed_analysis['student_positions'].append({
                'track_id': student.track_id,
                'bbox': student.bbox,
                'confidence': student.confidence,
                'suspicious_actions': student.suspicious_actions[-10:],  # Last 10 only
                'activity_score': student.activity_score
            })
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(suspicious_activities, risk_factors)
        
        # Determine status
        if risk_level >= 8:
            status = "CRITICAL"
            self.violation_count += 1
        elif risk_level >= 5:
            status = "WARNING"
        else:
            status = "NORMAL"
        
        return {
            'person_count': len(persons),
            'tracked_students': len(self.tracked_students),
            'prohibited_items': [
                {'item': item.class_name, 'confidence': item.confidence}
                for item in prohibited_items
            ],
            'suspicious_activities': suspicious_activities,
            'risk_level': risk_level,
            'status': status,
            'annotated_frame': annotated,
            'detailed_analysis': detailed_analysis,
            'violation_count': self.violation_count,
            'frame_timestamp': time.time(),
            'detections': [
                {
                    'class_id': d.class_id,
                    'class_name': d.class_name,
                    'confidence': d.confidence,
                    'bbox': d.bbox,
                    'is_person': d.is_person,
                    'is_prohibited': d.is_prohibited
                }
                for d in detections
            ]
        }
    
    def _calculate_risk_level(self, activities, risk_factors):
        """Calculate comprehensive risk level (0-10)"""
        base_risk = 0
        
        # Add risk from factors
        for factor, weight in risk_factors:
            base_risk += weight
        
        # Add risk from number of activities
        base_risk += min(3.0, len(activities) * 0.5)
        
        # Cap at 10
        return min(10.0, base_risk)
    
    def get_activity_summary(self):
        """Get summary - FIXED: Memory safe"""
        summary = {
            'total_violations': self.violation_count,
            'current_students': len(self.tracked_students),
            'recent_activities': list(self.activity_history)[-10:],  # Last 10 only
            'tracked_students_info': []
        }
        
        for track_id, student in list(self.tracked_students.items())[:10]:  # Max 10
            summary['tracked_students_info'].append({
                'track_id': track_id,
                'suspicious_actions': student.suspicious_actions[-5:],  # Last 5 only
                'activity_score': student.activity_score,
                'last_seen': student.last_seen
            })
        
        return summary
    
    def reset_tracking(self):
        """Reset tracking and activity history"""
        self.tracked_students.clear()
        self.activity_history.clear()
        self.violation_count = 0
        print("🔄 Tracking reset")
    
    def cleanup(self):
        """Manual cleanup"""
        print("🧹 ObjectDetector cleanup...")
        current_time = time.time()
        self._cleanup_old_tracks(current_time)
        print(f"   Tracked students: {len(self.tracked_students)}")
        print(f"   Activity history: {len(self.activity_history)}")
    
    def __del__(self):
        """Destructor"""
        try:
            self.cleanup()
        except:
            pass
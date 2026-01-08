"""
Enhanced Object Detector with YOLOv8 for Proctoring
Multi-person detection and activity monitoring
"""
import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from collections import deque
import time

@dataclass
class Detection:
    """Data class for detection results"""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    is_person: bool = False
    is_prohibited: bool = False
    track_id: Optional[int] = None
    timestamp: float = 0.0

@dataclass
class Student:
    """Data class for tracked student"""
    track_id: int
    bbox: List[float]
    confidence: float
    last_seen: float
    position_history: deque
    activity_score: float = 0.0
    suspicious_actions: List[str] = None
    
    def __post_init__(self):
        if self.suspicious_actions is None:
            self.suspicious_actions = []
        if self.position_history is None:
            self.position_history = deque(maxlen=20)

class ObjectDetector:
    """Enhanced object detector with student activity monitoring"""
    
    # Prohibited classes (COCO dataset)
    PROHIBITED_CLASSES = {
        67: 'cell phone',
        73: 'book',
        61: 'dining table',
        39: 'bottle',
        41: 'cup',
        76: 'scissors',
        63: 'laptop',
        62: 'toilet',  # For unusual objects
        77: 'teddy bear',  # For unusual objects
        27: 'backpack',
        28: 'umbrella'
    }
    
    # Suspicious activities
    SUSPICIOUS_ACTIONS = {
        'MULTIPLE_PERSONS': "Multiple students detected",
        'NO_PERSON': "No student in frame",
        'LOOKING_DOWN': "Looking down frequently",
        'LOOKING_SIDE': "Looking sideways frequently",
        'HEAD_TURNED': "Head turned away from screen",
        'PHONE_DETECTED': "Mobile phone detected",
        'BOOK_DETECTED': "Book or notes detected",
        'UNUSUAL_OBJECT': "Suspicious object detected",
        'MULTIPLE_DEVICES': "Multiple electronic devices",
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
            
            # Tracking and activity monitoring
            self.next_track_id = 0
            self.tracked_students = {}  # track_id -> Student
            self.activity_history = deque(maxlen=100)
            self.violation_count = 0
            
            # Alert thresholds
            self.max_students = 1  # Maximum allowed students
            self.max_absent_time = 5.0  # Max seconds without student
            self.proximity_threshold = 100  # Pixels for close proximity
            
            print(f"✅ YOLO loaded: {len(self.class_names)} classes")
            
        except Exception as e:
            print(f"❌ Failed to load YOLO: {e}")
            self.model = None
    
    def detect(self, frame, conf=None, classes=None):
        """Detect objects in frame with tracking"""
        if self.model is None:
            return [], frame
        
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
        current_time = time.time()
        
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
        """Register a new student for tracking"""
        student = Student(
            track_id=track_id,
            bbox=bbox.tolist(),
            confidence=confidence,
            last_seen=timestamp,
            position_history=deque(maxlen=20)
        )
        self.tracked_students[track_id] = student
        
        # Log new student
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
        
        # Add to position history
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        student.position_history.append((center_x, center_y, timestamp))
    
    def _cleanup_tracks(self, current_time):
        """Remove old tracks"""
        tracks_to_remove = []
        for track_id, student in self.tracked_students.items():
            if current_time - student.last_seen > 2.0:  # 2 seconds threshold
                tracks_to_remove.append(track_id)
                print(f"🎓 Student {track_id} left the frame")
                self._log_activity(f"Student {track_id} left the frame")
        
        for track_id in tracks_to_remove:
            del self.tracked_students[track_id]
    
    def _log_activity(self, activity):
        """Log suspicious activity"""
        log_entry = {
            'timestamp': time.time(),
            'activity': activity,
            'tracked_students': len(self.tracked_students)
        }
        self.activity_history.append(log_entry)
    
    def analyze_student_activity(self, frame):
        """
        Comprehensive analysis of student activities for cheating detection
        
        Returns:
            - Number of students
            - Suspicious activities
            - Risk assessment
            - Detailed analysis
        """
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
            'activity_timeline': list(self.activity_history)[-5:],  # Last 5 activities
            'proximity_warnings': [],
            'time_analysis': {}
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
        
        # Analyze student proximity (for collaboration detection)
        if len(persons) > 1:
            for i in range(len(persons)):
                for j in range(i + 1, len(persons)):
                    bbox1 = persons[i].bbox
                    bbox2 = persons[j].bbox
                    
                    # Calculate distance between persons
                    center1 = np.array([(bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2])
                    center2 = np.array([(bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2])
                    distance = np.linalg.norm(center1 - center2)
                    
                    if distance < self.proximity_threshold:
                        activity = self.SUSPICIOUS_ACTIONS['CLOSE_PROXIMITY']
                        suspicious_activities.append(activity)
                        risk_factors.append(('close_proximity', 2.0))
                        detailed_analysis['proximity_warnings'].append({
                            'student1': persons[i].track_id or i,
                            'student2': persons[j].track_id or j,
                            'distance': distance,
                            'threshold': self.proximity_threshold
                        })
        
        # Analyze tracked student movements
        for track_id, student in self.tracked_students.items():
            # Analyze movement patterns
            if len(student.position_history) >= 5:
                positions = list(student.position_history)
                movements = []
                
                for k in range(1, len(positions)):
                    x1, y1, t1 = positions[k-1]
                    x2, y2, t2 = positions[k]
                    distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    time_diff = t2 - t1
                    speed = distance / time_diff if time_diff > 0 else 0
                    movements.append(speed)
                
                avg_movement = np.mean(movements) if movements else 0
                if avg_movement > 50:  # High movement threshold
                    student.suspicious_actions.append("Excessive movement")
                    student.activity_score += 1.0
            
            # Store student info
            detailed_analysis['student_positions'].append({
                'track_id': student.track_id,
                'bbox': student.bbox,
                'confidence': student.confidence,
                'suspicious_actions': student.suspicious_actions,
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
            'frame_timestamp': time.time()
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
    
    def analyze_proctoring(self, frame):
        """
        Main proctoring analysis (compatibility wrapper)
        """
        return self.analyze_student_activity(frame)
    
    def draw_detections_with_activity(self, frame, analysis_result):
        """Draw enhanced detections with activity information"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Get detections from analysis
        detections = analysis_result.get('detections', [])
        
        # Draw bounding boxes
        for det in detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            
            # Color coding
            if det.is_person:
                color = (0, 255, 0)  # Green for person
                thickness = 2
                
                # Add track ID for persons
                if det.track_id is not None:
                    label = f"Student {det.track_id}: {det.confidence:.2f}"
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                    cv2.putText(annotated, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            elif det.is_prohibited:
                color = (0, 0, 255)  # Red for prohibited
                thickness = 3
                label = f"PROHIBITED: {det.class_name} {det.confidence:.2f}"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(annotated, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                color = (255, 0, 0)  # Blue for other
                thickness = 1
                label = f"{det.class_name} {det.confidence:.2f}"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                cv2.putText(annotated, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw activity information overlay
        self._draw_activity_overlay(annotated, analysis_result)
        
        return annotated
    
    def _draw_activity_overlay(self, frame, analysis_result):
        """Draw activity analysis overlay on frame"""
        h, w = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Draw header with status
        status = analysis_result.get('status', 'NORMAL')
        risk_level = analysis_result.get('risk_level', 0)
        person_count = analysis_result.get('person_count', 0)
        
        # Status color
        if status == "CRITICAL":
            status_color = (0, 0, 255)  # Red
        elif status == "WARNING":
            status_color = (0, 255, 255)  # Yellow
        else:
            status_color = (0, 255, 0)  # Green
        
        # Draw status bar
        cv2.rectangle(overlay, (0, 0), (w, 40), status_color, -1)
        cv2.rectangle(overlay, (0, 0), (w, 40), (255, 255, 255), 2)
        
        status_text = f"Status: {status} | Risk: {risk_level:.1f}/10 | Students: {person_count}"
        cv2.putText(overlay, status_text, (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw suspicious activities
        activities = analysis_result.get('suspicious_activities', [])
        if activities:
            y_offset = 50
            cv2.putText(overlay, "⚠️ Suspicious Activities:", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            y_offset += 25
            for i, activity in enumerate(activities[:3]):  # Show max 3
                cv2.putText(overlay, f"• {activity}", (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                y_offset += 20
        
        # Draw prohibited items
        prohibited_items = analysis_result.get('prohibited_items', [])
        if prohibited_items:
            y_offset = h - 100
            cv2.putText(overlay, "🚫 Prohibited Items:", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            y_offset += 25
            for i, item in enumerate(prohibited_items[:2]):  # Show max 2
                item_text = f"• {item['item']} ({item['confidence']:.2f})"
                cv2.putText(overlay, item_text, (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                y_offset += 20
        
        # Add alpha blending
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    def get_activity_summary(self):
        """Get summary of recent activities"""
        summary = {
            'total_violations': self.violation_count,
            'current_students': len(self.tracked_students),
            'recent_activities': list(self.activity_history)[-10:],
            'tracked_students_info': []
        }
        
        for track_id, student in self.tracked_students.items():
            summary['tracked_students_info'].append({
                'track_id': track_id,
                'suspicious_actions': student.suspicious_actions,
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


# Test function
def test_student_activity_detection():
    """Test the enhanced student activity detection"""
    detector = ObjectDetector()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    print("\n🎓 Testing Student Activity Detection...")
    print("This system detects:")
    print("1. Multiple students (cheating/collaboration)")
    print("2. Prohibited items (phones, books, etc.)")
    print("3. Student movements and activities")
    print("4. Suspicious proximity between students")
    print("Press 'q' to quit, 'r' to reset tracking")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze student activity
        result = detector.analyze_student_activity(frame)
        
        # Draw enhanced visualization
        annotated = detector.draw_detections_with_activity(frame, result)
        
        # Display
        cv2.imshow('Student Activity Detection', annotated)
        
        # Print status every 30 frames
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('r'):
            detector.reset_tracking()
            print("🔄 Tracking reset")
        
        # Print summary every 60 frames
        if cv2.getTickCount() % 60 == 0:
            print(f"\n📊 Current Status:")
            print(f"  Students: {result['person_count']}")
            print(f"  Tracked: {result['tracked_students']}")
            print(f"  Prohibited Items: {len(result['prohibited_items'])}")
            print(f"  Risk Level: {result['risk_level']:.1f}/10")
            print(f"  Status: {result['status']}")
            
            if result['suspicious_activities']:
                print(f"  ⚠️ Suspicious Activities: {result['suspicious_activities']}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Final summary
    summary = detector.get_activity_summary()
    print(f"\n📈 Session Summary:")
    print(f"Total Violations: {summary['total_violations']}")
    print(f"Activities Logged: {len(summary['recent_activities'])}")


if __name__ == "__main__":
    test_student_activity_detection()
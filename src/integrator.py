"""
Enhanced Vision Guardian with Student Activity Monitoring
"""
import cv2
import time
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque

class VisionGuardian:
    """Enhanced proctoring system with student activity monitoring"""
    
    def __init__(self, config: Dict = None):
        """Initialize with student monitoring"""
        # Default configuration
        self.config = {
            'enable_gaze': True,
            'enable_objects': True,
            'enable_student_monitoring': True,  # New: Student activity monitoring
            'save_output': True,
            'output_dir': 'proctoring_results',
            'gaze_confidence': 0.5,
            'object_confidence': 0.5,
            'max_students': 1,  # Maximum allowed students
            'violation_cooldown': 5,
            'activity_history_size': 100
        }
        
        if config:
            self.config.update(config)
        
        # Initialize components
        self.initialize_components()
        
        # Enhanced state tracking
        self.frame_count = 0
        self.violation_count = 0
        self.last_violation_time = 0
        self.start_time = time.time()
        
        # Student monitoring
        self.student_activities = deque(maxlen=self.config['activity_history_size'])
        self.cheating_attempts = []
        
        # Create output directory
        if self.config['save_output']:
            Path(self.config['output_dir']).mkdir(parents=True, exist_ok=True)
            print(f"📁 Output directory: {self.config['output_dir']}")
    
    def initialize_components(self):
        """Initialize all components"""
        self.gaze_tracker = None
        self.object_detector = None
        
        # Try to import and initialize gaze tracker
        if self.config.get('enable_gaze', True):
            try:
                from src.gaze_module import GazeTracker
                self.gaze_tracker = GazeTracker()
                print("✅ Gaze tracker initialized")
            except Exception as e:
                print(f"⚠️ Gaze tracker not available: {e}")
                self.gaze_tracker = None
        
        # Try to import and initialize enhanced object detector
        if self.config.get('enable_objects', True) or self.config.get('enable_student_monitoring', True):
            try:
                from src.object_module import ObjectDetector
                self.object_detector = ObjectDetector()
                print("✅ Enhanced object detector initialized (with student monitoring)")
            except Exception as e:
                print(f"⚠️ Object detector not available: {e}")
                self.object_detector = None
    
    def process_frame(self, frame, frame_id: int = None):
        """Process frame with enhanced student monitoring"""
        self.frame_count += 1
        if frame_id is None:
            frame_id = self.frame_count
        
        # Initialize enhanced results structure
        results = {
            'frame_id': frame_id,
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat(),
            'gaze_analysis': None,
            'object_analysis': None,
            'student_analysis': None,  # New: Student-specific analysis
            'violations': [],
            'suspicious_activities': [],
            'risk_score': 0,
            'is_cheating': False,
            'alert_level': 'NORMAL',
            'processing_time': 0,
            'student_count': 0,
            'cheating_indicators': []
        }
        
        start_process = time.time()
        
        # Gaze analysis
        if self.gaze_tracker:
            try:
                gaze_result = self.gaze_tracker.analyze_gaze(frame)
                results['gaze_analysis'] = gaze_result
                
                # Check for suspicious gaze patterns
                if gaze_result.get('level', 0) >= 2:
                    results['suspicious_activities'].append(f"GAZE_CRITICAL: {gaze_result.get('status')}")
                    results['cheating_indicators'].append('suspicious_gaze')
                elif gaze_result.get('level', 0) >= 1:
                    results['suspicious_activities'].append(f"GAZE_WARNING: {gaze_result.get('status')}")
            except Exception as e:
                results['violations'].append(f"GAZE_ERROR: {str(e)[:30]}")
        
        # Enhanced object and student analysis
        if self.object_detector:
            try:
                # Use enhanced student activity analysis
                analysis_result = self.object_detector.analyze_student_activity(frame)
                results['object_analysis'] = analysis_result
                results['student_analysis'] = analysis_result.get('detailed_analysis', {})
                
                # Extract student count
                results['student_count'] = analysis_result.get('person_count', 0)
                
                # Check for multiple students (cheating/collaboration)
                if results['student_count'] > self.config['max_students']:
                    violation_msg = f"MULTIPLE_STUDENTS: {results['student_count']} detected (max: {self.config['max_students']})"
                    results['violations'].append(violation_msg)
                    results['cheating_indicators'].append('multiple_students')
                    results['suspicious_activities'].append(violation_msg)
                
                # Check for prohibited items
                prohibited_items = analysis_result.get('prohibited_items', [])
                if prohibited_items:
                    for item in prohibited_items:
                        violation_msg = f"PROHIBITED_ITEM: {item['item']}"
                        results['violations'].append(violation_msg)
                        results['cheating_indicators'].append('prohibited_item')
                        results['suspicious_activities'].append(violation_msg)
                
                # Add suspicious activities from object detection
                suspicious_activities = analysis_result.get('suspicious_activities', [])
                results['suspicious_activities'].extend(suspicious_activities)
                
                # Store student activity
                if self.config.get('enable_student_monitoring', True):
                    self._record_student_activity(results)
                
            except Exception as e:
                results['violations'].append(f"OBJECT_ERROR: {str(e)[:30]}")
        
        # Calculate enhanced risk score
        results['risk_score'] = self.calculate_enhanced_risk_score(results)
        
        # Determine alert level with student-specific rules
        results['alert_level'] = self.determine_enhanced_alert_level(results)
        results['is_cheating'] = results['alert_level'] in ['WARNING', 'CRITICAL']
        
        # Record cheating attempt if detected
        if results['is_cheating']:
            self._record_cheating_attempt(results)
        
        # Save violation if needed
        if results['is_cheating'] and self.config['save_output']:
            self.save_enhanced_violation(frame, results)
        
        # Calculate processing time
        results['processing_time'] = round((time.time() - start_process) * 1000, 2)
        
        return results
    
    def _record_student_activity(self, results):
        """Record student activity for pattern analysis"""
        activity_record = {
            'timestamp': results['timestamp'],
            'frame_id': results['frame_id'],
            'student_count': results['student_count'],
            'suspicious_activities': results['suspicious_activities'].copy(),
            'risk_score': results['risk_score'],
            'alert_level': results['alert_level']
        }
        self.student_activities.append(activity_record)
    
    def _record_cheating_attempt(self, results):
        """Record detailed cheating attempt information"""
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'frame_id': results['frame_id'],
            'student_count': results['student_count'],
            'violations': results['violations'].copy(),
            'cheating_indicators': results['cheating_indicators'].copy(),
            'risk_score': results['risk_score'],
            'alert_level': results['alert_level'],
            'suspicious_activities': results['suspicious_activities'].copy()
        }
        self.cheating_attempts.append(attempt)
        self.violation_count += 1
    
    def calculate_enhanced_risk_score(self, results: Dict) -> int:
        """Calculate enhanced risk score with student monitoring"""
        risk = 0
        
        # Base risk from gaze
        gaze = results.get('gaze_analysis', {})
        gaze_level = gaze.get('level', 0)
        if gaze_level == 2:
            risk += 4  # Critical gaze
        elif gaze_level == 1:
            risk += 2  # Warning gaze
        
        # Risk from student count
        student_count = results.get('student_count', 0)
        if student_count == 0:
            risk += 4  # No student (cheating by absence)
        elif student_count > self.config['max_students']:
            risk += min(5, (student_count - self.config['max_students']) * 2)  # Multiple students
        
        # Risk from prohibited items
        prohibited_count = 0
        if results.get('object_analysis'):
            prohibited_count = len(results['object_analysis'].get('prohibited_items', []))
        risk += min(3, prohibited_count * 2)
        
        # Risk from suspicious activities
        activity_count = len(results.get('suspicious_activities', []))
        risk += min(3, activity_count)
        
        # Risk from cheating indicators
        indicator_count = len(results.get('cheating_indicators', []))
        risk += min(2, indicator_count)
        
        return min(10, risk)
    
    def determine_enhanced_alert_level(self, results: Dict) -> str:
        """Determine alert level with student-specific rules"""
        risk_score = results.get('risk_score', 0)
        violations = results.get('violations', [])
        student_count = results.get('student_count', 0)
        
        # Critical conditions (highest priority)
        critical_conditions = [
            student_count > self.config['max_students'],  # Multiple students
            student_count == 0,  # No student
            risk_score >= 8,  # Very high risk
            any('MULTIPLE_STUDENTS' in v for v in violations),  # Multiple students violation
            any('PROHIBITED_ITEM' in v for v in violations) and len(violations) >= 2  # Multiple prohibited items
        ]
        
        # Warning conditions
        warning_conditions = [
            risk_score >= 5,
            len(violations) >= 1,
            len(results.get('suspicious_activities', [])) >= 2,
            student_count > 1  # More than 1 student but within limit
        ]
        
        if any(critical_conditions):
            return 'CRITICAL'
        elif any(warning_conditions):
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def save_enhanced_violation(self, frame: np.ndarray, results: Dict):
        """Save enhanced violation data with student information"""
        # Cooldown check
        current_time = time.time()
        if current_time - self.last_violation_time < self.config.get('violation_cooldown', 5):
            return
        
        self.last_violation_time = current_time
        
        try:
            output_dir = Path(self.config['output_dir'])
            
            # Create violation directory
            violation_dir = output_dir / 'violations'
            violation_dir.mkdir(exist_ok=True)
            
            # Create students directory for student-specific violations
            students_dir = output_dir / 'students'
            students_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violation_{timestamp}_f{results['frame_id']:06d}_s{results['student_count']}.jpg"
            
            # Save annotated frame with student information
            annotated = self.annotate_frame_with_students(frame, results)
            image_path = violation_dir / filename
            cv2.imwrite(str(image_path), annotated)
            
            # Enhanced metadata with student information
            metadata = results.copy()
            metadata['saved_image'] = str(image_path)
            metadata['student_analysis'] = results.get('student_analysis', {})
            metadata['cheating_indicators'] = results.get('cheating_indicators', [])
            metadata['suspicious_activities'] = results.get('suspicious_activities', [])
            
            metadata_path = violation_dir / f"{filename}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Log student-specific violation
            if results['student_count'] > 0:
                student_log = {
                    'timestamp': metadata['datetime'],
                    'student_count': results['student_count'],
                    'violation_type': 'cheating_attempt',
                    'indicators': results['cheating_indicators'],
                    'image_path': str(image_path),
                    'metadata_path': str(metadata_path)
                }
                
                student_log_path = students_dir / f"student_log_{timestamp}.json"
                with open(student_log_path, 'w') as f:
                    json.dump(student_log, f, indent=2)
            
            print(f"⚠️ Violation #{self.violation_count} saved (Students: {results['student_count']})")
            
        except Exception as e:
            print(f"❌ Failed to save violation: {e}")
    
    def annotate_frame_with_students(self, frame: np.ndarray, results: Dict) -> np.ndarray:
        """Annotate frame with student information"""
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
        
        # Enhanced header with student count
        banner_height = 100
        cv2.rectangle(annotated, (0, 0), (w, banner_height), color, -1)
        
        # Title with student information
        student_count = results.get('student_count', 0)
        title = f"Vision Guardian - {alert_level} - Students: {student_count}"
        cv2.putText(annotated, title, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Enhanced info lines
        info_lines = [
            f"Frame: {results.get('frame_id', 0)} | Risk: {results.get('risk_score', 0)}/10",
            f"Students: {student_count} | Suspicious Activities: {len(results.get('suspicious_activities', []))}",
            f"Cheating Indicators: {len(results.get('cheating_indicators', []))}"
        ]
        
        for i, line in enumerate(info_lines):
            cv2.putText(annotated, line, (10, 55 + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Student-specific information
        y_offset = banner_height + 20
        
        # If multiple students detected, show warning
        if student_count > self.config['max_students']:
            warning_text = f"⚠️ MULTIPLE STUDENTS DETECTED: {student_count} (Allowed: {self.config['max_students']})"
            cv2.putText(annotated, warning_text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 30
        
        # Show cheating indicators
        cheating_indicators = results.get('cheating_indicators', [])
        if cheating_indicators:
            cv2.putText(annotated, "Cheating Indicators:", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
            y_offset += 25
            
            for i, indicator in enumerate(cheating_indicators[:3]):  # Show max 3
                indicator_text = f"• {indicator.replace('_', ' ').title()}"
                cv2.putText(annotated, indicator_text, (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                y_offset += 20
        
        # Draw student zones if applicable
        if student_count > 0:
            # Draw safe zone for single student
            zone_color = (0, 255, 0) if student_count <= self.config['max_students'] else (0, 0, 255)
            zone_thickness = 2 if student_count <= self.config['max_students'] else 4
            
            cv2.rectangle(annotated, (50, 50), (w-50, h-50), zone_color, zone_thickness)
            
            # Add zone label
            zone_label = "Single Student Zone" if student_count <= self.config['max_students'] else "MULTIPLE STUDENTS VIOLATION"
            cv2.putText(annotated, zone_label, (60, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 2)
        
        return annotated
    
    def get_student_analysis(self) -> Dict:
        """Get comprehensive student activity analysis"""
        recent_activities = list(self.student_activities)
        
        if not recent_activities:
            return {'status': 'no_activity_yet'}
        
        # Analyze activity patterns
        student_counts = [act['student_count'] for act in recent_activities]
        risk_scores = [act['risk_score'] for act in recent_activities]
        
        analysis = {
            'total_frames_analyzed': len(recent_activities),
            'average_student_count': np.mean(student_counts) if student_counts else 0,
            'max_student_count': max(student_counts) if student_counts else 0,
            'average_risk_score': np.mean(risk_scores) if risk_scores else 0,
            'max_risk_score': max(risk_scores) if risk_scores else 0,
            'cheating_attempts': len(self.cheating_attempts),
            'recent_violations': [
                {
                    'timestamp': attempt['timestamp'],
                    'student_count': attempt['student_count'],
                    'indicators': attempt['cheating_indicators']
                }
                for attempt in self.cheating_attempts[-5:]  # Last 5 attempts
            ],
            'activity_pattern': self._analyze_activity_pattern(recent_activities)
        }
        
        return analysis
    
    def _analyze_activity_pattern(self, activities):
        """Analyze patterns in student activities"""
        if len(activities) < 10:
            return {'status': 'insufficient_data'}
        
        # Analyze for patterns of cheating
        high_risk_periods = []
        current_period = None
        
        for activity in activities:
            if activity['risk_score'] >= 7:
                if current_period is None:
                    current_period = {
                        'start': activity['timestamp'],
                        'end': activity['timestamp'],
                        'max_risk': activity['risk_score'],
                        'student_count': activity['student_count']
                    }
                else:
                    current_period['end'] = activity['timestamp']
                    current_period['max_risk'] = max(current_period['max_risk'], activity['risk_score'])
            elif current_period is not None:
                high_risk_periods.append(current_period)
                current_period = None
        
        if current_period is not None:
            high_risk_periods.append(current_period)
        
        return {
            'high_risk_periods': high_risk_periods,
            'total_high_risk_periods': len(high_risk_periods),
            'pattern_detected': len(high_risk_periods) > 2  # If more than 2 high-risk periods
        }
    
    def get_enhanced_stats(self) -> Dict:
        """Get enhanced statistics with student monitoring"""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # Get student analysis
        student_analysis = self.get_student_analysis()
        
        return {
            'frames_processed': self.frame_count,
            'violations_detected': self.violation_count,
            'cheating_attempts': len(self.cheating_attempts),
            'fps': round(fps, 1),
            'elapsed_time': round(elapsed, 1),
            'student_analysis': student_analysis,
            'components_active': {
                'gaze': self.gaze_tracker is not None,
                'objects': self.object_detector is not None,
                'student_monitoring': self.config.get('enable_student_monitoring', False)
            }
        }
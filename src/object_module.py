"""
Optimized Object Detector with YOLOv8
Better performance and cleaner code
"""
import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class Detection:
    """Data class for detection results"""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    is_person: bool = False
    is_prohibited: bool = False

class ObjectDetector:
    """Optimized object detector with YOLOv8"""
    
    # Prohibited classes (COCO dataset)
    PROHIBITED_CLASSES = {
        67: 'cell phone',
        73: 'book',
        61: 'dining table',
        39: 'bottle',
        41: 'cup'
    }
    
    def __init__(self, model_path='models/yolov8n.pt', device='cpu'):
        """Initialize detector"""
        print(f"🔧 Loading YOLO model: {model_path}")
        
        try:
            self.model = YOLO(model_path)
            self.device = device
            self.class_names = self.model.names
            
            # Detection parameters
            self.conf_threshold = 0.5
            self.iou_threshold = 0.45
            
            print(f"✅ YOLO loaded: {len(self.class_names)} classes")
            
        except Exception as e:
            print(f"❌ Failed to load YOLO: {e}")
            self.model = None
    
    def detect(self, frame, conf=None, classes=None):
        """Detect objects in frame"""
        if self.model is None:
            return [], frame
        
        # Run inference
        results = self.model(
            frame,
            conf=conf or self.conf_threshold,
            iou=self.iou_threshold,
            classes=classes or [0] + list(self.PROHIBITED_CLASSES.keys()),
            device=self.device,
            verbose=False
        )
        
        detections = []
        for result in results:
            if result.boxes is None:
                continue
                
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()
                
                detection = Detection(
                    class_id=cls_id,
                    class_name=self.class_names[cls_id],
                    confidence=conf,
                    bbox=bbox.tolist(),
                    is_person=cls_id == 0,
                    is_prohibited=cls_id in self.PROHIBITED_CLASSES
                )
                detections.append(detection)
        
        # Get annotated frame
        annotated = results[0].plot() if results else frame.copy()
        
        return detections, annotated
    
    def analyze_proctoring(self, frame):
        """Analyze frame for proctoring violations"""
        detections, annotated = self.detect(frame)
        
        # Count persons and prohibited items
        person_count = sum(1 for d in detections if d.is_person)
        prohibited_items = [
            d for d in detections 
            if d.is_prohibited and d.confidence > 0.5
        ]
        
        # Check violations
        violations = []
        level = 0
        
        if person_count == 0:
            violations.append("NO_PERSON")
            level = 2
        elif person_count > 1:
            violations.append("MULTIPLE_PERSONS")
            level = 2
        
        if prohibited_items:
            violations.extend([f"PROHIBITED_{item.class_name.upper()}" 
                             for item in prohibited_items])
            level = 2
        
        # Determine status
        status = "CRITICAL" if level == 2 else "WARNING" if violations else "NORMAL"
        
        return {
            'person_count': person_count,
            'prohibited_items': [
                {'item': item.class_name, 'confidence': item.confidence}
                for item in prohibited_items
            ],
            'violations': violations,
            'level': level,
            'status': status,
            'annotated_frame': annotated,
            'detections': detections
        }
    
    def draw_detections(self, frame, detections):
        """Draw custom detections on frame"""
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det.bbox)
            
            # Color coding
            if det.is_person:
                color = (0, 255, 0)  # Green
            elif det.is_prohibited:
                color = (0, 0, 255)  # Red
            else:
                color = (255, 0, 0)  # Blue
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return annotated
"""
Fixed Gaze Tracker - Proper Normalization & Math
FIXED: Eye-relative normalization, face size handling, robust detection
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

class GazeTracker:
    """Fixed gaze tracker with proper normalization"""
    
    # Landmark indices for MediaPipe Face Mesh (478 landmarks)
    LANDMARK_INDICES = {
        # Left eye
        'left_eye_inner': 133, 'left_eye_outer': 33,
        'left_eye_top': 159, 'left_eye_bottom': 145,
        'left_iris': 468,
        # Right eye
        'right_eye_inner': 362, 'right_eye_outer': 263,
        'right_eye_top': 386, 'right_eye_bottom': 374,
        'right_iris': 473,
        # Face pose
        'nose_tip': 1, 'forehead': 10, 'chin': 152,
        'left_mouth': 61, 'right_mouth': 291
    }
    
    def __init__(self, model_path='models/face_landmarker.task'):
        """Initialize gaze tracker"""
        print(f"🔧 Initializing Gaze Tracker with: {model_path}")
        
        self.detector = None
        self.is_initialized = False
        
        try:
            # Ensure model directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Download model if not exists
            if not os.path.exists(model_path):
                print(f"📥 Downloading MediaPipe model...")
                model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                urllib.request.urlretrieve(model_url, model_path)
                print(f"✅ Model downloaded: {model_path}")
            
            # Create options
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                running_mode=vision.RunningMode.IMAGE
            )
            
            # Create detector
            self.detector = vision.FaceLandmarker.create_from_options(options)
            self.is_initialized = True
            print("✅ Gaze tracker initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize gaze tracker: {e}")
            self.is_initialized = False
    
    def _get_coordinates(self, landmarks, idx, img_shape):
        """Get pixel coordinates for landmark"""
        if idx >= len(landmarks):
            return None
        
        lm = landmarks[idx]
        x = lm.x * img_shape[1]  # Convert normalized to pixels
        y = lm.y * img_shape[0]
        return np.array([x, y])
    
    def _calculate_eye_dimensions(self, eye_landmarks, img_shape):
        """Calculate eye width and height in pixels"""
        inner = eye_landmarks['inner']
        outer = eye_landmarks['outer']
        top = eye_landmarks['top']
        bottom = eye_landmarks['bottom']
        
        if any(coord is None for coord in [inner, outer, top, bottom]):
            return None, None
        
        # Eye width (horizontal distance)
        eye_width = np.linalg.norm(outer - inner)
        
        # Eye height (vertical distance)
        eye_height = np.linalg.norm(bottom - top)
        
        return eye_width, eye_height
    
    def calculate_gaze_ratio(self, landmarks, img_shape):
        """
        Calculate gaze ratios - FIXED: Normalized relative to eye size
        
        Returns:
            Tuple of (horizontal_ratio, vertical_ratio)
            - 0.0 = extreme left/up
            - 0.5 = center
            - 1.0 = extreme right/down
        """
        try:
            # Get all eye coordinates
            left_eye = {
                'inner': self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_eye_inner'], img_shape),
                'outer': self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_eye_outer'], img_shape),
                'top': self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_eye_top'], img_shape),
                'bottom': self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_eye_bottom'], img_shape),
                'iris': self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_iris'], img_shape)
            }
            
            right_eye = {
                'inner': self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_eye_inner'], img_shape),
                'outer': self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_eye_outer'], img_shape),
                'top': self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_eye_top'], img_shape),
                'bottom': self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_eye_bottom'], img_shape),
                'iris': self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_iris'], img_shape)
            }
            
            # Check if all coordinates are valid
            if any(coord is None for eye in [left_eye, right_eye] for coord in eye.values()):
                return 0.5, 0.5  # Return neutral position
            
            # Calculate eye dimensions
            left_eye_width, left_eye_height = self._calculate_eye_dimensions(left_eye, img_shape)
            right_eye_width, right_eye_height = self._calculate_eye_dimensions(right_eye, img_shape)
            
            if not all([left_eye_width, left_eye_height, right_eye_width, right_eye_height]):
                return 0.5, 0.5
            
            # HORIZONTAL GAZE (Left-Right)
            # Calculate iris position relative to eye center
            left_eye_center = (left_eye['inner'] + left_eye['outer']) / 2
            right_eye_center = (right_eye['inner'] + right_eye['outer']) / 2
            
            # Horizontal offset from eye center
            left_h_offset = left_eye['iris'][0] - left_eye_center[0]
            right_h_offset = right_eye['iris'][0] - right_eye_center[0]
            
            # FIXED: Normalize by EYE WIDTH (not frame width)
            # Typical iris movement is about ±30% of eye width
            left_h_ratio = 0.5 + (left_h_offset / (left_eye_width * 0.6))  # 0.6 = max movement range
            right_h_ratio = 0.5 + (right_h_offset / (right_eye_width * 0.6))
            
            # Average both eyes
            avg_h_ratio = (left_h_ratio + right_h_ratio) / 2
            avg_h_ratio = np.clip(avg_h_ratio, 0.0, 1.0)
            
            # VERTICAL GAZE (Up-Down)
            # Calculate iris position relative to eye top/bottom
            left_v_offset = left_eye['iris'][1] - left_eye['top'][1]
            right_v_offset = right_eye['iris'][1] - right_eye['top'][1]
            
            # FIXED: Normalize by EYE HEIGHT
            left_v_ratio = left_v_offset / left_eye_height
            right_v_ratio = right_v_offset / right_eye_height
            
            # Average both eyes
            avg_v_ratio = (left_v_ratio + right_v_ratio) / 2
            avg_v_ratio = np.clip(avg_v_ratio, 0.0, 1.0)
            
            return avg_h_ratio, avg_v_ratio
            
        except Exception as e:
            print(f"⚠️ Gaze calculation error: {e}")
            return 0.5, 0.5
    
    def calculate_head_pose(self, landmarks, img_shape):
        """
        Calculate head pose - FIXED: Better head rotation detection
        """
        try:
            # Get key facial points
            nose = self._get_coordinates(landmarks, self.LANDMARK_INDICES['nose_tip'], img_shape)
            left_eye_inner = self._get_coordinates(landmarks, self.LANDMARK_INDICES['left_eye_inner'], img_shape)
            right_eye_inner = self._get_coordinates(landmarks, self.LANDMARK_INDICES['right_eye_inner'], img_shape)
            chin = self._get_coordinates(landmarks, self.LANDMARK_INDICES['chin'], img_shape)
            forehead = self._get_coordinates(landmarks, self.LANDMARK_INDICES['forehead'], img_shape)
            
            if any(coord is None for coord in [nose, left_eye_inner, right_eye_inner, chin, forehead]):
                return None
            
            # Calculate eye center
            eye_center = (left_eye_inner + right_eye_inner) / 2
            
            # HORIZONTAL HEAD ROTATION
            # Calculate horizontal offset of nose from eye center
            face_width = np.linalg.norm(right_eye_inner - left_eye_inner)
            nose_offset_x = nose[0] - eye_center[0]
            
            # FIXED: Normalize by face width
            head_rotation = nose_offset_x / (face_width * 0.5)  # ±1.0 range
            head_rotation = np.clip(head_rotation, -1.0, 1.0)
            
            # VERTICAL HEAD TILT
            # Calculate vertical offset of nose from eye center
            face_height = np.linalg.norm(chin - forehead)
            nose_offset_y = nose[1] - eye_center[1]
            
            # Normalize by face height
            head_tilt = nose_offset_y / (face_height * 0.3)  # ±1.0 range
            head_tilt = np.clip(head_tilt, -1.0, 1.0)
            
            # Determine looking down
            # If nose is significantly below eyes, person is looking down
            is_looking_down = head_tilt > 0.3
            
            return {
                'head_rotation': round(float(head_rotation), 3),
                'head_tilt': round(float(head_tilt), 3),
                'is_looking_down': is_looking_down,
                'face_width': round(float(face_width), 2),
                'face_height': round(float(face_height), 2)
            }
            
        except Exception as e:
            print(f"⚠️ Head pose error: {e}")
            return None
    
    def analyze_gaze(self, frame):
        """
        Main analysis method - FIXED: Better thresholds and logic
        """
        if not self.is_initialized:
            return {
                "status": "MODEL_NOT_LOADED", 
                "level": 2, 
                "h_ratio": 0.5, 
                "v_ratio": 0.5
            }
        
        try:
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create mediapipe image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Detect
            detection_result = self.detector.detect(mp_image)
            
            if not detection_result.face_landmarks:
                return {
                    "status": "NO_FACE_DETECTED", 
                    "level": 2, 
                    "h_ratio": 0.5, 
                    "v_ratio": 0.5
                }
            
            landmarks = detection_result.face_landmarks[0]
            h, w = frame.shape[:2]
            
            # Calculate gaze and pose
            h_ratio, v_ratio = self.calculate_gaze_ratio(landmarks, (h, w))
            head_pose = self.calculate_head_pose(landmarks, (h, w))
            
            # Determine status and level with FIXED thresholds
            status = "Looking Center"
            level = 0
            
            # HORIZONTAL GAZE DETECTION
            # Center range: 0.35 - 0.65 (30% margin on each side)
            if h_ratio < 0.35:
                status = "Looking Right"
                level = 1
                if h_ratio < 0.25:  # Extreme right
                    level = 2
            elif h_ratio > 0.65:
                status = "Looking Left"
                level = 1
                if h_ratio > 0.75:  # Extreme left
                    level = 2
            
            # VERTICAL GAZE DETECTION
            # Center range: 0.30 - 0.70
            if v_ratio > 0.70:
                status = "Looking Down"
                level = max(level, 2)  # Looking down is always critical
            elif v_ratio < 0.30:
                status = "Looking Up"
                level = max(level, 1)
            
            # HEAD POSE ADJUSTMENTS
            if head_pose:
                # Head turned significantly
                if abs(head_pose['head_rotation']) > 0.4:
                    direction = "Left" if head_pose['head_rotation'] < 0 else "Right"
                    status = f"Head Turned {direction}"
                    level = max(level, 2)
                elif abs(head_pose['head_rotation']) > 0.25:
                    level = max(level, 1)
                
                # Looking down (head tilt)
                if head_pose['is_looking_down'] and level < 2:
                    status = "Looking Down (Head Tilt)"
                    level = 2
            
            return {
                "status": status,
                "level": level,
                "h_ratio": round(h_ratio, 3),
                "v_ratio": round(v_ratio, 3),
                "head_pose": head_pose,
                "confidence": "HIGH" if head_pose else "MEDIUM"
            }
            
        except Exception as e:
            print(f"❌ Gaze analysis error: {e}")
            return {
                "status": f"ERROR: {str(e)[:30]}", 
                "level": 2, 
                "h_ratio": 0.5, 
                "v_ratio": 0.5
            }
    
    def visualize(self, frame, analysis):
        """Visualize results on frame"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Color coding based on level
        colors = [(0, 255, 0), (0, 255, 255), (0, 0, 255)]  # Green, Yellow, Red
        level = min(analysis.get("level", 0), 2)
        color = colors[level]
        
        # Draw status text
        status = analysis.get("status", "UNKNOWN")
        cv2.putText(annotated, f"Gaze: {status}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add ratios if available
        h_ratio = analysis.get("h_ratio", 0.5)
        v_ratio = analysis.get("v_ratio", 0.5)
        cv2.putText(annotated, f"H: {h_ratio:.2f}, V: {v_ratio:.2f}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add head pose if available
        head_pose = analysis.get("head_pose")
        if head_pose:
            rotation = head_pose.get('head_rotation', 0)
            tilt = head_pose.get('head_tilt', 0)
            cv2.putText(annotated, f"Head: R={rotation:.2f}, T={tilt:.2f}", (20, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw gaze indicator
        indicator_y = 150
        indicator_width = 200
        indicator_x_start = 20
        
        # Horizontal indicator
        cv2.rectangle(annotated, (indicator_x_start, indicator_y), 
                     (indicator_x_start + indicator_width, indicator_y + 10), 
                     (100, 100, 100), -1)
        
        h_pos = int(indicator_x_start + h_ratio * indicator_width)
        cv2.circle(annotated, (h_pos, indicator_y + 5), 8, color, -1)
        
        # Vertical indicator
        cv2.rectangle(annotated, (indicator_x_start, indicator_y + 20), 
                     (indicator_x_start + 10, indicator_y + 20 + indicator_width), 
                     (100, 100, 100), -1)
        
        v_pos = int(indicator_y + 20 + v_ratio * indicator_width)
        cv2.circle(annotated, (indicator_x_start + 5, v_pos), 8, color, -1)
        
        return annotated


# Test function
def test():
    """Quick test function"""
    tracker = GazeTracker()
    
    if not tracker.is_initialized:
        print("❌ Gaze tracker failed to initialize")
        return
    
    cap = cv2.VideoCapture(0)
    print("\n🎥 Testing gaze tracker... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = tracker.analyze_gaze(frame)
        annotated = tracker.visualize(frame, result)
        
        # Print status every 30 frames
        if cap.get(cv2.CAP_PROP_POS_FRAMES) % 30 == 0:
            print(f"Status: {result['status']}, Level: {result['level']}, "
                  f"H: {result['h_ratio']:.2f}, V: {result['v_ratio']:.2f}")
        
        cv2.imshow('Gaze Test', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test()
"""
Simplified Gaze Tracker - Fixed Imports
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class GazeTracker:
    """Simplified gaze tracker with proper imports"""
    
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
        
        try:
            # Download model if not exists
            import urllib.request
            import os
            
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
        """Get coordinates for landmark"""
        if idx >= len(landmarks):
            return None
        
        lm = landmarks[idx]
        return np.array([lm.x * img_shape[1], lm.y * img_shape[0]])
    
    def calculate_gaze_ratio(self, landmarks, img_shape):
        """Calculate gaze ratios (simplified)"""
        try:
            coords = {}
            
            # Get required coordinates
            required_keys = ['left_eye_inner', 'left_eye_outer', 'left_eye_top', 
                           'left_eye_bottom', 'left_iris', 'right_eye_inner', 
                           'right_eye_outer', 'right_eye_top', 'right_eye_bottom', 
                           'right_iris']
            
            for key in required_keys:
                idx = self.LANDMARK_INDICES[key]
                coord = self._get_coordinates(landmarks, idx, img_shape)
                if coord is None:
                    return 0.5, 0.5  # Return neutral position
                coords[key] = coord
            
            # Simplified gaze calculation
            # Horizontal: Compare iris to eye center
            left_eye_center = (coords['left_eye_inner'] + coords['left_eye_outer']) / 2
            right_eye_center = (coords['right_eye_inner'] + coords['right_eye_outer']) / 2
            
            left_h_offset = coords['left_iris'][0] - left_eye_center[0]
            right_h_offset = coords['right_iris'][0] - right_eye_center[0]
            
            # Normalize to -1 to 1 range
            left_h_ratio = 0.5 + (left_h_offset / (img_shape[1] * 0.05))
            right_h_ratio = 0.5 + (right_h_offset / (img_shape[1] * 0.05))
            
            avg_h_ratio = np.clip((left_h_ratio + right_h_ratio) / 2, 0.0, 1.0)
            
            # Vertical: Simple ratio based on iris position in eye
            left_v_ratio = (coords['left_iris'][1] - coords['left_eye_top'][1]) / \
                          (coords['left_eye_bottom'][1] - coords['left_eye_top'][1])
            right_v_ratio = (coords['right_iris'][1] - coords['right_eye_top'][1]) / \
                           (coords['right_eye_bottom'][1] - coords['right_eye_top'][1])
            
            avg_v_ratio = np.clip((left_v_ratio + right_v_ratio) / 2, 0.0, 1.0)
            
            return avg_h_ratio, avg_v_ratio
            
        except Exception as e:
            print(f"⚠️ Gaze calculation error: {e}")
            return 0.5, 0.5
    
    def calculate_head_pose(self, landmarks, img_shape):
        """Calculate head pose (simplified)"""
        try:
            # Get key points
            nose_idx = self.LANDMARK_INDICES['nose_tip']
            left_eye_idx = self.LANDMARK_INDICES['left_eye_inner']
            right_eye_idx = self.LANDMARK_INDICES['right_eye_inner']
            
            # Get normalized coordinates
            nose = landmarks[nose_idx]
            left_eye = landmarks[left_eye_idx]
            right_eye = landmarks[right_eye_idx]
            
            # Simple head rotation based on eye positions
            eye_distance = abs(left_eye.x - right_eye.x)
            nose_offset = nose.x - 0.5  # Center is 0.5
            
            # Estimate head rotation (-1 to 1)
            head_rotation = nose_offset * 2
            
            # Estimate looking down based on eye positions
            eye_level = (left_eye.y + right_eye.y) / 2
            is_looking_down = eye_level > 0.6  # Eyes are low in frame
            
            return {
                'head_rotation': round(head_rotation, 3),
                'is_looking_down': is_looking_down,
                'eye_level': round(eye_level, 3)
            }
            
        except Exception as e:
            print(f"⚠️ Head pose error: {e}")
            return None
    
    def analyze_gaze(self, frame):
        """Main analysis method"""
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
            
            # Determine status and level
            status = "Looking Center"
            level = 0
            
            # Horizontal gaze
            if h_ratio < 0.35:
                status = "Looking Right"
                level = 1
            elif h_ratio > 0.65:
                status = "Looking Left"
                level = 1
            
            # Vertical gaze
            if v_ratio > 0.70:
                status = "Looking Down (Suspicious)"
                level = 2
            elif v_ratio < 0.30:
                status = "Looking Up"
                level = max(level, 1)
            
            # Head pose adjustments
            if head_pose:
                if head_pose.get('is_looking_down', False) and level < 2:
                    status = "Looking Down (Head Pose)"
                    level = 2
                
                if abs(head_pose.get('head_rotation', 0)) > 0.2:
                    direction = "Left" if head_pose['head_rotation'] < 0 else "Right"
                    status = f"Head Turned {direction}"
                    level = max(level, 1)
            
            return {
                "status": status,
                "level": level,
                "h_ratio": round(h_ratio, 3),
                "v_ratio": round(v_ratio, 3),
                "head_pose": head_pose
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
        
        # Color coding
        colors = [(0, 255, 0), (0, 255, 255), (0, 0, 255)]
        color = colors[min(analysis.get("level", 0), 2)]
        
        # Draw status
        status = analysis.get("status", "UNKNOWN")
        level = analysis.get("level", 0)
        
        cv2.putText(annotated, f"Gaze: {status}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add ratios if available
        h_ratio = analysis.get("h_ratio", 0.5)
        v_ratio = analysis.get("v_ratio", 0.5)
        cv2.putText(annotated, f"H: {h_ratio:.2f}, V: {v_ratio:.2f}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated


# Simple test
def test():
    """Quick test function"""
    tracker = GazeTracker()
    
    cap = cv2.VideoCapture(0)
    print("\n🎥 Testing gaze tracker... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = tracker.analyze_gaze(frame)
        annotated = tracker.visualize(frame, result)
        
        cv2.imshow('Gaze Test', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test()
# unified_proctoring_improved.py
import cv2
import mediapipe as mp
from ultralytics import YOLO
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import numpy as np
import urllib.request

# Function to download models if not present
def download_models():
    """Download required models if they don't exist"""
    os.makedirs('models', exist_ok=True)
    
    mp_model_path = 'models/face_landmarker.task'
    if not os.path.exists(mp_model_path):
        print("📥 Downloading MediaPipe Face Landmarker model...")
        mp_model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        try:
            urllib.request.urlretrieve(mp_model_url, mp_model_path)
            print(f"✅ Downloaded: {mp_model_path}")
        except Exception as e:
            print(f"❌ Error downloading model: {e}")
            return False
    else:
        print(f"✅ Model already exists: {mp_model_path}")
    
    return True

# Download models first
if not download_models():
    print("Failed to download models. Exiting...")
    exit(1)

# Initialize models
MODEL_PATH = 'models/face_landmarker.task'
try:
    base_options_mp = python.BaseOptions(model_asset_path=MODEL_PATH)
    options_mp = vision.FaceLandmarkerOptions(
        base_options=base_options_mp,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        running_mode=vision.RunningMode.IMAGE,
        min_face_detection_confidence=0.3,
        min_face_presence_confidence=0.3,
        num_faces=1  # Expect single student
    )
    landmarker = vision.FaceLandmarker.create_from_options(options_mp)
    print("✅ MediaPipe FaceLandmarker initialized")
except Exception as e:
    print(f"❌ Error initializing MediaPipe: {e}")
    landmarker = None

# YOLO model initialization
try:
    model_yolo = YOLO('yolov8n.pt')
    print("✅ YOLO model initialized")
except Exception as e:
    print(f"❌ Error initializing YOLO: {e}")
    model_yolo = None

def get_correct_landmark_indices():
    """
    Return CORRECT landmark indices for MediaPipe FaceLandmarker
    Based on MediaPipe documentation: https://developers.google.com/mediapipe/solutions/vision/face_landmarker
    """
    # CORRECT INDICES for MediaPipe FaceMesh (468 landmarks)
    # Left eye
    LEFT_EYE_INNER = 133   # Left eye corner inner
    LEFT_EYE_OUTER = 33    # Left eye corner outer
    LEFT_EYE_TOP = 159     # Left eye top
    LEFT_EYE_BOTTOM = 145  # Left eye bottom
    LEFT_IRIS = 468        # Left iris center (NEW in updated model)
    
    # Right eye
    RIGHT_EYE_INNER = 362  # Right eye corner inner
    RIGHT_EYE_OUTER = 263  # Right eye corner outer
    RIGHT_EYE_TOP = 386    # Right eye top
    RIGHT_EYE_BOTTOM = 374 # Right eye bottom
    RIGHT_IRIS = 473       # Right iris center (NEW in updated model)
    
    return {
        'left_eye_inner': LEFT_EYE_INNER,
        'left_eye_outer': LEFT_EYE_OUTER,
        'left_eye_top': LEFT_EYE_TOP,
        'left_eye_bottom': LEFT_EYE_BOTTOM,
        'left_iris': LEFT_IRIS,
        'right_eye_inner': RIGHT_EYE_INNER,
        'right_eye_outer': RIGHT_EYE_OUTER,
        'right_eye_top': RIGHT_EYE_TOP,
        'right_eye_bottom': RIGHT_EYE_BOTTOM,
        'right_iris': RIGHT_IRIS
    }

def calculate_gaze_ratio_improved(facial_landmarks, img_shape, indices):
    """
    IMPROVED and ROBUST gaze calculation
    Returns normalized gaze ratios (0-1 range)
    """
    try:
        # Get indices
        left_outer = indices['left_eye_outer']
        left_inner = indices['left_eye_inner']
        left_top = indices['left_eye_top']
        left_bottom = indices['left_eye_bottom']
        left_iris = indices['left_iris']
        
        right_outer = indices['right_eye_outer']
        right_inner = indices['right_eye_inner']
        right_top = indices['right_eye_top']
        right_bottom = indices['right_eye_bottom']
        right_iris = indices['right_iris']
        
        # Check if we have enough landmarks
        required_indices = [left_outer, left_inner, left_top, left_bottom, left_iris,
                           right_outer, right_inner, right_top, right_bottom, right_iris]
        
        if max(required_indices) >= len(facial_landmarks):
            print(f"⚠️ Not enough landmarks. Have {len(facial_landmarks)}, need {max(required_indices)+1}")
            return None, None
        
        # Convert landmarks to pixel coordinates
        def get_coords(idx):
            lm = facial_landmarks[idx]
            return np.array([lm.x * img_shape[1], lm.y * img_shape[0]])
        
        # LEFT EYE CALCULATION
        l_outer = get_coords(left_outer)
        l_inner = get_coords(left_inner)
        l_top = get_coords(left_top)
        l_bottom = get_coords(left_bottom)
        l_iris = get_coords(left_iris)
        
        # Horizontal ratio for left eye
        # Distance from iris to outer corner / total eye width
        l_eye_width = np.linalg.norm(l_inner - l_outer)
        l_iris_to_outer = np.linalg.norm(l_iris - l_outer)
        
        # Ensure no division by zero and normalize
        if l_eye_width > 0:
            l_h_ratio = l_iris_to_outer / l_eye_width
        else:
            l_h_ratio = 0.5
        
        # Vertical ratio for left eye
        l_eye_height = np.linalg.norm(l_bottom - l_top)
        l_iris_to_top = np.linalg.norm(l_iris - l_top)
        
        if l_eye_height > 0:
            l_v_ratio = l_iris_to_top / l_eye_height
        else:
            l_v_ratio = 0.5
        
        # RIGHT EYE CALCULATION
        r_outer = get_coords(right_outer)
        r_inner = get_coords(right_inner)
        r_top = get_coords(right_top)
        r_bottom = get_coords(right_bottom)
        r_iris = get_coords(right_iris)
        
        # Horizontal ratio for right eye
        r_eye_width = np.linalg.norm(r_outer - r_inner)
        r_iris_to_inner = np.linalg.norm(r_iris - r_inner)
        
        if r_eye_width > 0:
            r_h_ratio = r_iris_to_inner / r_eye_width
        else:
            r_h_ratio = 0.5
        
        # Vertical ratio for right eye
        r_eye_height = np.linalg.norm(r_bottom - r_top)
        r_iris_to_top = np.linalg.norm(r_iris - r_top)
        
        if r_eye_height > 0:
            r_v_ratio = r_iris_to_top / r_eye_height
        else:
            r_v_ratio = 0.5
        
        # AVERAGE BOTH EYES (more robust)
        avg_h_ratio = (l_h_ratio + r_h_ratio) / 2
        avg_v_ratio = (l_v_ratio + r_v_ratio) / 2
        
        # NORMALIZE to reasonable range (0-1)
        # Clamp values to prevent extreme ratios
        avg_h_ratio = max(0.0, min(1.0, avg_h_ratio))
        avg_v_ratio = max(0.0, min(1.0, avg_v_ratio))
        
        # DEBUG: Print for verification
        # print(f"DEBUG - L: H={l_h_ratio:.3f}, V={l_v_ratio:.3f} | R: H={r_h_ratio:.3f}, V={r_v_ratio:.3f}")
        # print(f"DEBUG - Avg: H={avg_h_ratio:.3f}, V={avg_v_ratio:.3f}")
        
        return round(avg_h_ratio, 3), round(avg_v_ratio, 3)
        
    except Exception as e:
        print(f"❌ Gaze calculation error: {e}")
        return None, None

def analyze_gaze_improved(facial_landmarks, img_shape):
    """
    Improved gaze analysis with proper thresholding
    """
    # Get correct indices
    indices = get_correct_landmark_indices()
    
    # Calculate ratios
    h_ratio, v_ratio = calculate_gaze_ratio_improved(facial_landmarks, img_shape, indices)
    
    if h_ratio is None or v_ratio is None:
        return "GAZE_CALC_ERROR", None, None, 0
    
    # Classification with adjusted thresholds
    status = "Normal"
    flag_level = 0  # 0: Normal, 1: Warning, 2: Critical
    
    # HORIZONTAL GAZE (Left/Right)
    # Normal range: 0.35 to 0.65
    if h_ratio < 0.35:
        status = "Looking Right"
        flag_level = 1
    elif h_ratio > 0.65:
        status = "Looking Left"
        flag_level = 1
    
    # VERTICAL GAZE (Up/Down) - More sensitive
    # Normal range: 0.40 to 0.60
    if v_ratio > 0.70:  # Looking DOWN (most suspicious for cheating)
        status = "Looking Down (Suspicious)"
        flag_level = 2
    elif v_ratio < 0.30:  # Looking UP
        status = "Looking Up"
        if flag_level < 1:
            flag_level = 1
    
    # If both horizontal and vertical deviations
    if (h_ratio < 0.35 or h_ratio > 0.65) and (v_ratio > 0.70 or v_ratio < 0.30):
        status = "Looking Away (Multiple)"
        flag_level = 2
    
    # Calculate confidence based on deviation from center
    h_confidence = 1.0 - abs(0.5 - h_ratio) * 2  # 0.5 is center
    v_confidence = 1.0 - abs(0.5 - v_ratio) * 2
    confidence = (h_confidence + v_confidence) / 2
    
    return status, h_ratio, v_ratio, flag_level

def run_unified_proctoring_improved(image_path):
    """
    IMPROVED unified proctoring with better gaze detection
    """
    # Load the image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error: Could not load image from {image_path}")
        return None, {"error": "Image not loaded"}

    # Convert to RGB for MediaPipe
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_height, img_width = img.shape[:2]

    proctoring_results = {
        "filename": os.path.basename(image_path),
        "gaze_status": "NO_FACE_DETECTED",
        "h_ratio": None,
        "v_ratio": None,
        "gaze_suspect_level": 2,  # High suspect level if no face
        "person_count": 0,
        "prohibited_objects": [],
        "yolo_suspect_level": 0,
        "face_detected": False
    }

    # ========== IMPROVED GAZE DETECTION ==========
    if landmarker is not None:
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            landmarker_result = landmarker.detect(mp_image)

            if landmarker_result and landmarker_result.face_landmarks:
                proctoring_results["face_detected"] = True
                
                # Use the first face detected
                facial_landmarks = landmarker_result.face_landmarks[0]
                
                # Print number of landmarks for debugging
                print(f"📊 Face detected with {len(facial_landmarks)} landmarks")
                
                # Improved gaze analysis
                gaze_status, h_ratio, v_ratio, gaze_suspect_level = analyze_gaze_improved(
                    facial_landmarks, (img_height, img_width)
                )
                
                proctoring_results.update({
                    "gaze_status": gaze_status,
                    "h_ratio": h_ratio,
                    "v_ratio": v_ratio,
                    "gaze_suspect_level": gaze_suspect_level
                })
                
                print(f"👁️ Gaze Analysis: {gaze_status} (H: {h_ratio}, V: {v_ratio})")
            else:
                print("👁️ No face detected by MediaPipe")
        except Exception as e:
            print(f"⚠️ MediaPipe error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ MediaPipe not initialized, skipping gaze analysis")

    # Start with original image for annotations
    annotated_image = img.copy()

    # ========== YOLO OBJECT DETECTION ==========
    if model_yolo is not None:
        try:
            # Higher confidence threshold for better accuracy
            yolo_results = model_yolo(img, conf=0.5, classes=[0, 67, 73], verbose=False)

            person_count = 0
            prohibited_objects = []
            yolo_suspect_level = 0

            for result in yolo_results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    label = model_yolo.names[class_id]

                    if label == 'person' and confidence > 0.5:
                        person_count += 1
                        # print(f"👤 Person detected (conf: {confidence:.2f})")
                    
                    if label in ['cell phone', 'book'] and confidence > 0.5:
                        prohibited_objects.append(f"{label} ({confidence:.2f})")
                        yolo_suspect_level = max(yolo_suspect_level, 2)
                        print(f"📱 Prohibited: {label} (conf: {confidence:.2f})")

            proctoring_results.update({
                "person_count": person_count,
                "prohibited_objects": list(set(prohibited_objects)),
                "yolo_suspect_level": yolo_suspect_level
            })
            
            print(f"📊 YOLO Summary: Persons={person_count}, Prohibited={prohibited_objects}")
            
            # Draw YOLO detections
            if len(yolo_results) > 0:
                yolo_plotted_image = yolo_results[0].plot()
                annotated_image = yolo_plotted_image
                
        except Exception as e:
            print(f"⚠️ YOLO error: {e}")
    else:
        print("⚠️ YOLO not initialized, skipping object detection")

    # ========== COMBINED ANALYSIS LOGIC ==========
    final_proctoring_status = "NORMAL: All Clear"
    final_suspect_level = 0

    # Rule prioritization
    if proctoring_results['prohibited_objects']:
        obj_names = ", ".join([obj.split('(')[0].strip() for obj in proctoring_results['prohibited_objects']])
        final_proctoring_status = f"CRITICAL: PROHIBITED OBJECTS DETECTED! ({obj_names})"
        final_suspect_level = 3
    elif proctoring_results['person_count'] == 0:
        final_proctoring_status = "ALERT: STUDENT MISSING!"
        final_suspect_level = 2
    elif proctoring_results['person_count'] > 1:
        final_proctoring_status = f"ALERT: {proctoring_results['person_count']} PEOPLE DETECTED!"
        final_suspect_level = 2
    elif proctoring_results['gaze_suspect_level'] == 2:
        final_proctoring_status = "WARNING: SUSPICIOUS GAZE (Looking Down/Away)!"
        final_suspect_level = 2
    elif proctoring_results['gaze_suspect_level'] == 1:
        final_proctoring_status = "WARNING: MINOR GAZE DEVIATION"
        final_suspect_level = 1
    elif not proctoring_results['face_detected'] and proctoring_results['person_count'] > 0:
        final_proctoring_status = "WARNING: FACE NOT CLEARLY VISIBLE"
        final_suspect_level = 1

    proctoring_results.update({
        "final_proctoring_status": final_proctoring_status,
        "final_suspect_level": final_suspect_level
    })

    print(f"🎯 Combined Analysis: {final_proctoring_status}")

    # ========== ADD STATUS BANNER ==========
    status_color = (0, 255, 0)  # Green for Normal (BGR format)
    if final_suspect_level == 1:
        status_color = (0, 255, 255)  # Yellow
    elif final_suspect_level == 2:
        status_color = (0, 165, 255)  # Orange
    elif final_suspect_level == 3:
        status_color = (0, 0, 255)  # Red

    img_height, img_width, _ = annotated_image.shape
    banner_height = max(60, int(img_height * 0.12))
    
    # Draw banner
    cv2.rectangle(annotated_image, (0, 0), (img_width, banner_height), status_color, -1)
    
    # Add text
    font_scale = 0.7
    thickness = 2
    
    # Calculate text size
    (text_width, text_height), baseline = cv2.getTextSize(
        final_proctoring_status, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )
    
    # Adjust font scale if text is too wide
    if text_width > img_width - 20:
        font_scale = 0.5
        (text_width, text_height), baseline = cv2.getTextSize(
            final_proctoring_status, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
    
    text_x = max(10, (img_width - text_width) // 2)
    text_y = (banner_height + text_height) // 2
    
    cv2.putText(annotated_image, final_proctoring_status, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    return annotated_image, proctoring_results

def save_results_to_csv(results_list, filename="proctoring_results.csv"):
    """Save all results to CSV file"""
    import pandas as pd
    import csv
    
    if not results_list:
        print("No results to save")
        return
    
    # Create directory if not exists
    os.makedirs('reports', exist_ok=True)
    filepath = os.path.join('reports', filename)
    
    # Define fieldnames
    fieldnames = [
        'filename', 'gaze_status', 'h_ratio', 'v_ratio', 
        'gaze_suspect_level', 'person_count', 'prohibited_objects',
        'yolo_suspect_level', 'final_proctoring_status', 'final_suspect_level'
    ]
    
    # Write to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results_list:
            # Clean up the result for CSV
            cleaned_result = {}
            for key in fieldnames:
                if key in result:
                    if isinstance(result[key], list):
                        cleaned_result[key] = ';'.join(result[key])
                    else:
                        cleaned_result[key] = result[key]
                else:
                    cleaned_result[key] = ''
            writer.writerow(cleaned_result)
    
    print(f"📊 Results saved to: {filepath}")
    return filepath

def generate_summary_report(results_list):
    """Generate summary report from results"""
    if not results_list:
        print("No results to generate report")
        return
    
    total_images = len(results_list)
    
    # Count different statuses
    normal_count = sum(1 for r in results_list if r.get('final_suspect_level', 0) == 0)
    warning_count = sum(1 for r in results_list if r.get('final_suspect_level', 0) == 1)
    alert_count = sum(1 for r in results_list if r.get('final_suspect_level', 0) == 2)
    critical_count = sum(1 for r in results_list if r.get('final_suspect_level', 0) == 3)
    
    # Count prohibited objects
    prohibited_count = sum(1 for r in results_list if r.get('prohibited_objects', []))
    
    # Count gaze issues
    gaze_issues = sum(1 for r in results_list if r.get('gaze_suspect_level', 0) > 0)
    
    # Count presence issues
    presence_issues = sum(1 for r in results_list if r.get('person_count', 0) != 1)
    
    # Create summary
    summary = {
        'total_images': total_images,
        'normal': normal_count,
        'warning': warning_count,
        'alert': alert_count,
        'critical': critical_count,
        'with_prohibited_objects': prohibited_count,
        'with_gaze_issues': gaze_issues,
        'with_presence_issues': presence_issues,
        'normal_percentage': (normal_count / total_images) * 100 if total_images > 0 else 0,
        'suspicious_percentage': ((total_images - normal_count) / total_images) * 100 if total_images > 0 else 0
    }
    
    # Save summary
    import json
    os.makedirs('reports', exist_ok=True)
    summary_path = os.path.join('reports', 'summary_report.json')
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📈 Summary report saved to: {summary_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PROCTORING SUMMARY REPORT")
    print("="*60)
    print(f"Total Images Analyzed: {summary['total_images']}")
    print(f"Normal: {summary['normal']} ({summary['normal_percentage']:.1f}%)")
    print(f"Suspicious: {total_images - normal_count} ({summary['suspicious_percentage']:.1f}%)")
    print(f"Critical Cases (Prohibited Objects): {summary['with_prohibited_objects']}")
    print(f"Gaze Issues Detected: {summary['with_gaze_issues']}")
    print(f"Presence Issues: {summary['with_presence_issues']}")
    print("="*60)
    
    return summary

def process_folder_improved(folder_path, max_images=None, save_outputs=True):
    """Process folder with improved gaze detection"""
    import glob
    
    # Get all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    all_images = []
    
    for ext in image_extensions:
        all_images.extend(glob.glob(os.path.join(folder_path, ext)))
    
    if not all_images:
        print(f"❌ No images found in {folder_path}")
        return []
    
    # Limit if specified
    if max_images:
        all_images = all_images[:max_images]
    
    print(f"📁 Found {len(all_images)} images in folder")
    
    all_results = []
    
    # Create output directory
    if save_outputs:
        output_dir = "improved_outputs"
        os.makedirs(output_dir, exist_ok=True)
    
    # Process each image
    for i, img_path in enumerate(all_images):
        print(f"\n{'='*50}")
        print(f"📊 Processing {i+1}/{len(all_images)}: {os.path.basename(img_path)}")
        print('='*50)
        
        try:
            annotated_img, results = run_unified_proctoring_improved(img_path)
            
            if annotated_img is not None and results is not None:
                all_results.append(results)
                
                # Save annotated image
                if save_outputs:
                    output_path = os.path.join(output_dir, f"processed_{os.path.basename(img_path)}")
                    cv2.imwrite(output_path, annotated_img)
                    print(f"💾 Saved to: {output_path}")
                
                # Print brief summary
                print(f"  👁️ Gaze: {results.get('gaze_status', 'N/A')}")
                print(f"  👥 Persons: {results.get('person_count', 0)}")
                print(f"  📱 Prohibited: {results.get('prohibited_objects', [])}")
                print(f"  🎯 Status: {results.get('final_proctoring_status', 'N/A')}")
            else:
                print(f"❌ Failed to process: {os.path.basename(img_path)}")
                
        except Exception as e:
            print(f"❌ Error processing {img_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save all results
    if all_results:
        csv_path = save_results_to_csv(all_results, "improved_proctoring_results.csv")
        summary = generate_summary_report(all_results)
        
        print(f"\n✅ Processing complete!")
        print(f"📊 Processed {len(all_results)} images successfully")
        print(f"📁 Results saved in 'reports/' folder")
        print(f"🖼️ Annotated images saved in 'improved_outputs/' folder")
    
    return all_results

def main():
    """Main function"""
    print("="*60)
    print("🎯 IMPROVED VISION GUARDIAN PROCTORING SYSTEM")
    print("="*60)
    print("✅ Features: Improved Gaze Detection | Object Detection | Presence Check")
    print("="*60)
    
    # Get folder path from user
    folder_path = input("\n📁 Enter the folder path containing images: ").strip()
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        print("Please enter a valid folder path.")
        return
    
    # Ask for maximum images
    max_images_input = input("Enter maximum number of images to process (press Enter for all): ").strip()
    max_images = None
    if max_images_input:
        try:
            max_images = int(max_images_input)
            print(f"🔢 Will process maximum {max_images} images")
        except ValueError:
            print("⚠️ Invalid number. Will process all images.")
            max_images = None
    
    # Process the folder
    print(f"\n🚀 Starting improved proctoring analysis...")
    results = process_folder_improved(folder_path, max_images=max_images, save_outputs=True)
    
    print("\n" + "="*60)
    print("✅ IMPROVED PROCTORING ANALYSIS COMPLETED!")
    print("="*60)
    
    # Keep console open
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")




"""
Configuration for Vision Guardian Backend
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'
MODELS_DIR = BASE_DIR / 'models'
LOGS_DIR = BASE_DIR / 'logs'
SCREENSHOTS_DIR = BASE_DIR / 'screenshots'
REPORTS_DIR = BASE_DIR / 'reports'

# Create directories
for directory in [TEMPLATE_DIR, STATIC_DIR, MODELS_DIR, LOGS_DIR, SCREENSHOTS_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# AI Configuration
AI_CONFIG = {
    'enable_yolo': True,
    'enable_gaze': True,
    'enable_integrity': True,
    'yolo_model_path': MODELS_DIR / 'yolov8n.pt',
    'yolo_classes': [0, 67, 73],  # person, cell phone, book
    'yolo_conf_threshold': 0.5,
    'yolo_iou_threshold': 0.45,
    'max_students': 1,
    'save_output': False,
    'frame_skip': 2,  # Process every 2nd frame
    'target_fps': 15
}

# Integrity Auditor Configuration
INTEGRITY_CONFIG = {
    'ai_model_path': MODELS_DIR / 'ai_detector',
    'stylometry_model_path': MODELS_DIR / 'stylometry_model.pkl',
    'plagiarism_threshold': 75,
    'ai_detection_threshold': 50
}

# Flask Configuration
FLASK_CONFIG = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True,
    'threaded': True
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'vision_guardian.log'
}

# Print configuration
def print_config():
    """Print current configuration"""
    print("=" * 60)
    print("🔧 VISION GUARDIAN CONFIGURATION")
    print("=" * 60)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"AI Enabled: YOLO={AI_CONFIG['enable_yolo']}, "
          f"Gaze={AI_CONFIG['enable_gaze']}, "
          f"Integrity={AI_CONFIG['enable_integrity']}")
    print(f"YOLO Model: {AI_CONFIG['yolo_model_path']}")
    print("=" * 60)
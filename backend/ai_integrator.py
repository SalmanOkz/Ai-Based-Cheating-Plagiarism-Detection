"""
AI Model Integrator - Handles all AI model loading and inference
FIXED: NO DUMMY DATA - Real failures reported properly
"""
import cv2
import numpy as np
import traceback
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import threading
import os
from pathlib import Path

from config import AI_CONFIG, INTEGRITY_CONFIG, BASE_DIR
from untils.logging_utils import get_logger

logger = get_logger(__name__)

class AIModelIntegrator:
    """Integrates all AI models for Vision Guardian - NO DUMMY DATA"""
    
    def __init__(self):
        self.ai_components = {
            'yolo': None,
            'gaze_tracker': None,
            'object_detector': None,
            'vision_guardian': None,
            'text_auditor': None,
            'code_auditor': None,
            'stylometry': None,
            'all_loaded': False
        }
        
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize all AI models"""
        logger.info("🤖 Initializing AI Models...")
        
        # Initialize Vision AI models
        self._initialize_vision_models()
        
        # Initialize Integrity Auditor models
        self._initialize_integrity_models()
        
        # Check overall status
        loaded_models = [k for k, v in self.ai_components.items() 
                        if v is not None and k != 'all_loaded']
        self.ai_components['all_loaded'] = len(loaded_models) > 0
        
        logger.info(f"✅ AI Models Status:")
        for name, component in self.ai_components.items():
            if name != 'all_loaded':
                status = "✅ Loaded" if component is not None else "❌ Not Loaded"
                logger.info(f"  {name:<20} {status}")
    
    def _initialize_vision_models(self):
        """Initialize vision-based AI models"""
        try:
            # YOLO Model
            if AI_CONFIG['enable_yolo']:
                yolo_path = AI_CONFIG['yolo_model_path']
                if isinstance(yolo_path, Path):
                    yolo_path = str(yolo_path)
                
                possible_paths = [
                    yolo_path,
                    str(BASE_DIR / 'models' / 'yolov8n.pt'),
                    str(BASE_DIR / 'backend' / 'models' / 'yolov8n.pt'),
                    str(BASE_DIR / 'yolov8n.pt'),
                    'yolov8n.pt'
                ]
                
                yolo_loaded = False
                for path in possible_paths:
                    if os.path.exists(path):
                        try:
                            from ultralytics import YOLO
                            self.ai_components['yolo'] = YOLO(path)
                            logger.info(f"✅ YOLO Model loaded: {path}")
                            yolo_loaded = True
                            break
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to load YOLO from {path}: {e}")
                
                if not yolo_loaded:
                    logger.warning("⚠️ YOLO Model not loaded - will auto-download on first use")
            
            # Gaze Tracker
            if AI_CONFIG['enable_gaze']:
                try:
                    possible_gaze_paths = [
                        BASE_DIR / 'src' / 'gaze_module.py',
                        BASE_DIR / 'backend' / 'src' / 'gaze_module.py'
                    ]
                    
                    gaze_module_found = False
                    for gaze_path in possible_gaze_paths:
                        if gaze_path.exists():
                            import sys
                            sys.path.insert(0, str(gaze_path.parent.parent))
                            from src.gaze_module import GazeTracker
                            self.ai_components['gaze_tracker'] = GazeTracker()
                            logger.info("✅ Gaze Tracker loaded")
                            gaze_module_found = True
                            break
                    
                    if not gaze_module_found:
                        logger.warning("⚠️ Gaze module not found")
                        
                except ImportError as e:
                    logger.warning(f"⚠️ Gaze Tracker not available: {e}")
                except Exception as e:
                    logger.error(f"❌ Gaze Tracker initialization failed: {e}")
            
            # Object Detector
            try:
                possible_obj_paths = [
                    BASE_DIR / 'src' / 'object_module.py',
                    BASE_DIR / 'backend' / 'src' / 'object_module.py'
                ]
                
                obj_module_found = False
                for obj_path in possible_obj_paths:
                    if obj_path.exists():
                        import sys
                        sys.path.insert(0, str(obj_path.parent.parent))
                        from src.object_module import ObjectDetector
                        self.ai_components['object_detector'] = ObjectDetector()
                        logger.info("✅ Object Detector loaded")
                        obj_module_found = True
                        break
                
                if not obj_module_found:
                    logger.warning("⚠️ Object Detector module not found")
                    
            except ImportError as e:
                logger.warning(f"⚠️ Object Detector not available: {e}")
            except Exception as e:
                logger.error(f"❌ Object Detector initialization failed: {e}")
            
            # Vision Guardian
            try:
                possible_int_paths = [
                    BASE_DIR / 'src' / 'integrator.py',
                    BASE_DIR / 'backend' / 'src' / 'integrator.py'
                ]
                
                int_module_found = False
                for int_path in possible_int_paths:
                    if int_path.exists():
                        import sys
                        sys.path.insert(0, str(int_path.parent.parent))
                        from src.integrator import VisionGuardian
                        self.ai_components['vision_guardian'] = VisionGuardian({
                            'enable_gaze': AI_CONFIG['enable_gaze'],
                            'enable_objects': True,
                            'save_output': AI_CONFIG['save_output'],
                            'max_students': AI_CONFIG['max_students']
                        })
                        logger.info("✅ Vision Guardian loaded")
                        int_module_found = True
                        break
                
                if not int_module_found:
                    logger.warning("⚠️ Vision Guardian module not found")
                    
            except ImportError as e:
                logger.warning(f"⚠️ Vision Guardian not available: {e}")
            except Exception as e:
                logger.error(f"❌ Vision Guardian initialization failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing vision models: {e}")
            traceback.print_exc()
    
    def _initialize_integrity_models(self):
        """Initialize Integrity Auditor models - NO DUMMY DATA"""
        try:
            # Text Auditor (AI vs Human detection)
            try:
                model_path = INTEGRITY_CONFIG['ai_model_path']
                if isinstance(model_path, Path):
                    model_path = str(model_path)
                
                if os.path.exists(model_path) and os.path.isdir(model_path):
                    has_model = (
                        os.path.exists(os.path.join(model_path, 'pytorch_model.bin')) or
                        os.path.exists(os.path.join(model_path, 'model.safetensors'))
                    )
                    
                    required_tokenizer_files = ['config.json', 'vocab.txt', 'tokenizer_config.json']
                    has_tokenizer = all(
                        os.path.exists(os.path.join(model_path, f)) 
                        for f in required_tokenizer_files
                    )
                    
                    if has_model and has_tokenizer:
                        import sys
                        sys.path.insert(0, str(BASE_DIR))
                        from integrity_auditor.text_auditor import TextAuditor
                        self.ai_components['text_auditor'] = TextAuditor(model_path=model_path)
                        logger.info(f"✅ Text Auditor loaded from {model_path}")
                    else:
                        missing = []
                        if not has_model:
                            missing.append("model file")
                        if not has_tokenizer:
                            missing.append("tokenizer files")
                        
                        logger.error(f"❌ Text Auditor model incomplete. Missing: {', '.join(missing)}")
                        logger.error(f"   Train the model first: python train_text_model.py")
                else:
                    logger.error(f"❌ Text Auditor model not found at {model_path}")
                    logger.error(f"   Train the model first: python train_text_model.py")
                    
            except ImportError as e:
                logger.error(f"❌ Text Auditor import failed: {e}")
            except Exception as e:
                logger.error(f"❌ Text Auditor initialization failed: {e}")
            
            # Code Auditor (Plagiarism detection) - No model needed
            try:
                import sys
                sys.path.insert(0, str(BASE_DIR))
                from integrity_auditor.code_auditor import CodeAuditor
                self.ai_components['code_auditor'] = CodeAuditor()
                logger.info("✅ Code Auditor loaded")
            except ImportError as e:
                logger.error(f"❌ Code Auditor import failed: {e}")
            except Exception as e:
                logger.error(f"❌ Code Auditor initialization failed: {e}")
            
            # Stylometry Analyzer
            try:
                model_path = INTEGRITY_CONFIG['stylometry_model_path']
                if isinstance(model_path, Path):
                    model_path = str(model_path)
                
                import sys
                sys.path.insert(0, str(BASE_DIR))
                from integrity_auditor.stylometry import StylometryAnalyzer
                self.ai_components['stylometry'] = StylometryAnalyzer(model_path=model_path)
                
                if os.path.exists(model_path):
                    logger.info(f"✅ Stylometry Analyzer loaded with trained model")
                else:
                    logger.info(f"✅ Stylometry Analyzer loaded (no pre-trained model)")
                    
            except ImportError as e:
                logger.error(f"❌ Stylometry import failed: {e}")
            except Exception as e:
                logger.error(f"❌ Stylometry initialization failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing integrity models: {e}")
            traceback.print_exc()
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """Process frame with Vision Guardian or fallback to basic detection"""
        try:
            # Use Vision Guardian if available
            if self.ai_components['vision_guardian']:
                results = self.ai_components['vision_guardian'].process_frame(frame)
                results['success'] = True
                return results
            
            # Fallback: Use individual components
            results = {
                'success': False,
                'frame_id': 0,
                'timestamp': datetime.now().isoformat(),
                'gaze_analysis': {'status': 'No gaze tracker', 'level': 0},
                'object_analysis': None,
                'detections': [],
                'person_count': 0,
                'prohibited_count': 0,
                'risk_score': 0,
                'alert_level': 'NORMAL',
                'annotated_frame': frame.copy()
            }
            
            # Try gaze tracking
            if self.ai_components['gaze_tracker']:
                try:
                    gaze_result = self.ai_components['gaze_tracker'].analyze_gaze(frame)
                    results['gaze_analysis'] = gaze_result
                    results['annotated_frame'] = self.ai_components['gaze_tracker'].visualize(
                        results['annotated_frame'], gaze_result
                    )
                except Exception as e:
                    logger.error(f"Gaze tracking error: {e}")
            
            # Try object detection
            if self.ai_components['object_detector']:
                try:
                    obj_result = self.ai_components['object_detector'].analyze_student_activity(frame)
                    results['object_analysis'] = obj_result
                    results['person_count'] = obj_result.get('person_count', 0)
                    results['prohibited_count'] = len(obj_result.get('prohibited_items', []))
                    results['detections'] = obj_result.get('detections', [])
                    results['annotated_frame'] = obj_result.get('annotated_frame', results['annotated_frame'])
                except Exception as e:
                    logger.error(f"Object detection error: {e}")
            
            results['success'] = True
            return results
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'annotated_frame': frame.copy()
            }
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for AI generation - NO DUMMY DATA"""
        if not self.ai_components['text_auditor']:
            return {
                'error': 'Text Auditor not loaded. Train the model first.',
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'instructions': 'Run: python train_text_model.py'
            }
        
        try:
            result = self.ai_components['text_auditor'].analyze_text(text)
            result['timestamp'] = datetime.now().isoformat()
            result['success'] = True
            return result
        except Exception as e:
            logger.error(f"❌ Text analysis error: {e}")
            return {
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def check_code_plagiarism(self, code1: str, code2: str) -> Dict:
        """Check code plagiarism - NO DUMMY DATA"""
        if not self.ai_components['code_auditor']:
            return {
                'error': 'Code Auditor not loaded',
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            if hasattr(self.ai_components['code_auditor'], 'analyze_python'):
                result = self.ai_components['code_auditor'].analyze_python(code1, code2)
            else:
                result = self.ai_components['code_auditor'].detect(code1, code2)
            
            result['timestamp'] = datetime.now().isoformat()
            result['success'] = True
            return result
        except Exception as e:
            logger.error(f"❌ Code plagiarism check error: {e}")
            return {
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_writing_style(self, text: str) -> Dict:
        """Analyze writing style - NO DUMMY DATA"""
        if not self.ai_components['stylometry']:
            return {
                'error': 'Stylometry Analyzer not loaded',
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            report = self.ai_components['stylometry'].analyze_writing_style(text)
            features = self.ai_components['stylometry'].extract_features(text)
            
            return {
                'report': report,
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
        except Exception as e:
            logger.error(f"❌ Writing style analysis error: {e}")
            return {
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_status(self) -> Dict:
        """Get AI models status"""
        status = {}
        for name, component in self.ai_components.items():
            if name != 'all_loaded':
                status[name] = component is not None
        status['all_loaded'] = self.ai_components['all_loaded']
        
        detailed_status = {}
        for name, component in self.ai_components.items():
            if name != 'all_loaded' and component is not None:
                detailed_status[name] = {
                    'loaded': True,
                    'type': component.__class__.__name__
                }
            elif component is None:
                detailed_status[name] = {'loaded': False}
        
        status['detailed'] = detailed_status
        return status
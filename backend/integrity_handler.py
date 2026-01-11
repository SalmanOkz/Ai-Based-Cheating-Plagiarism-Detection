"""
Integrity Handler - Manages Integrity Auditor operations
"""
import os
import json
from typing import Dict, List
from datetime import datetime

from config import REPORTS_DIR
from utils.logging_utils import get_logger
from utils.file_utils import save_json, read_file, write_file

logger = get_logger(__name__)

class IntegrityHandler:
    """Handles integrity audit operations"""
    
    def __init__(self, ai_integrator):
        self.ai_integrator = ai_integrator
        self.audit_logs = []
        self.max_logs = 100
        
        # Ensure reports directory exists
        REPORTS_DIR.mkdir(exist_ok=True)
        
        logger.info("🛡️ Integrity Handler initialized")
    
    def analyze_text_content(self, text: str) -> Dict:
        """Analyze text content for integrity"""
        results = {
            'text_analysis': {},
            'style_analysis': {},
            'overall_verdict': 'PENDING',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Text analysis (AI vs Human)
            text_result = self.ai_integrator.analyze_text(text)
            results['text_analysis'] = text_result
            
            # Style analysis
            style_result = self.ai_integrator.analyze_writing_style(text)
            results['style_analysis'] = style_result
            
            # Determine overall verdict
            if 'error' in text_result:
                results['overall_verdict'] = 'ANALYSIS_ERROR'
            elif text_result.get('is_ai_generated', False):
                results['overall_verdict'] = 'AI_GENERATED'
            else:
                results['overall_verdict'] = 'HUMAN_WRITTEN'
            
            # Log the audit
            self._log_audit('text_analysis', results)
            
            # Save report
            self._save_text_report(results, text[:100])
            
        except Exception as e:
            logger.error(f"❌ Text analysis error: {e}")
            results['error'] = str(e)
            results['overall_verdict'] = 'ERROR'
        
        return results
    
    def check_code_plagiarism(self, code1: str, code2: str, 
                            language: str = 'python') -> Dict:
        """Check code plagiarism between two code snippets"""
        results = {
            'plagiarism_analysis': {},
            'language': language,
            'overall_verdict': 'PENDING',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Run plagiarism check
            plagiarism_result = self.ai_integrator.check_code_plagiarism(code1, code2)
            results['plagiarism_analysis'] = plagiarism_result
            
            # Determine verdict
            if 'error' in plagiarism_result:
                results['overall_verdict'] = 'ANALYSIS_ERROR'
            elif plagiarism_result.get('is_plagiarized', False):
                results['overall_verdict'] = 'PLAGIARISM_DETECTED'
            else:
                results['overall_verdict'] = 'ORIGINAL_CODE'
            
            # Log the audit
            self._log_audit('code_plagiarism', results)
            
            # Save report
            self._save_code_report(results, code1[:50], code2[:50])
            
        except Exception as e:
            logger.error(f"❌ Code plagiarism check error: {e}")
            results['error'] = str(e)
            results['overall_verdict'] = 'ERROR'
        
        return results
    
    def compare_code_files(self, file1_path: str, file2_path: str) -> Dict:
        """Compare two code files for plagiarism"""
        try:
            # Read files
            code1 = read_file(file1_path)
            code2 = read_file(file2_path)
            
            if not code1 or not code2:
                return {
                    'error': 'Could not read files',
                    'file1': file1_path,
                    'file2': file2_path
                }
            
            # Get file extensions
            ext1 = os.path.splitext(file1_path)[1].lower()
            ext2 = os.path.splitext(file2_path)[1].lower()
            
            # Check if same language
            if ext1 != ext2:
                return {
                    'error': 'Files must be of same language',
                    'file1_extension': ext1,
                    'file2_extension': ext2
                }
            
            # Determine language
            language_map = {
                '.py': 'python',
                '.java': 'java',
                '.js': 'javascript',
                '.cpp': 'cpp',
                '.c': 'c'
            }
            
            language = language_map.get(ext1, 'unknown')
            
            # Run plagiarism check
            return self.check_code_plagiarism(code1, code2, language)
            
        except Exception as e:
            logger.error(f"❌ File comparison error: {e}")
            return {'error': str(e)}
    
    def _log_audit(self, audit_type: str, results: Dict):
        """Log audit activity"""
        log_entry = {
            'type': audit_type,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        self.audit_logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.audit_logs) > self.max_logs:
            self.audit_logs.pop(0)
    
    def _save_text_report(self, results: Dict, text_sample: str):
        """Save text analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = REPORTS_DIR / f"text_analysis_{timestamp}.json"
        
        report = {
            'report_id': f"TEXT_{timestamp}",
            'analysis_type': 'text_integrity',
            'text_sample': text_sample,
            'results': results,
            'summary': self._generate_text_summary(results)
        }
        
        save_json(report, filename)
        logger.info(f"📄 Text report saved: {filename}")
    
    def _save_code_report(self, results: Dict, code1_sample: str, code2_sample: str):
        """Save code plagiarism report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = REPORTS_DIR / f"code_plagiarism_{timestamp}.json"
        
        report = {
            'report_id': f"CODE_{timestamp}",
            'analysis_type': 'code_plagiarism',
            'code_samples': {
                'code1_sample': code1_sample,
                'code2_sample': code2_sample
            },
            'results': results,
            'summary': self._generate_code_summary(results)
        }
        
        save_json(report, filename)
        logger.info(f"📄 Code report saved: {filename}")
    
    def _generate_text_summary(self, results: Dict) -> Dict:
        """Generate text analysis summary"""
        text_analysis = results.get('text_analysis', {})
        style_analysis = results.get('style_analysis', {})
        
        return {
            'verdict': results.get('overall_verdict', 'UNKNOWN'),
            'ai_confidence': text_analysis.get('ai_confidence', 0),
            'human_confidence': text_analysis.get('human_confidence', 0),
            'is_ai_generated': text_analysis.get('is_ai_generated', False),
            'features_extracted': style_analysis.get('features', {}).get('word_count', 0)
        }
    
    def _generate_code_summary(self, results: Dict) -> Dict:
        """Generate code plagiarism summary"""
        plagiarism = results.get('plagiarism_analysis', {})
        
        return {
            'verdict': results.get('overall_verdict', 'UNKNOWN'),
            'similarity': plagiarism.get('similarity_percentage', 0),
            'is_plagiarized': plagiarism.get('is_plagiarized', False),
            'language': results.get('language', 'unknown')
        }
    
    def get_audit_logs(self, limit: int = 10) -> List[Dict]:
        """Get recent audit logs"""
        return self.audit_logs[-limit:] if self.audit_logs else []
    
    def get_stats(self) -> Dict:
        """Get integrity handler statistics"""
        return {
            'total_audits': len(self.audit_logs),
            'recent_audits': len(self.audit_logs[-10:]),
            'text_audits': sum(1 for log in self.audit_logs if log['type'] == 'text_analysis'),
            'code_audits': sum(1 for log in self.audit_logs if log['type'] == 'code_plagiarism'),
            'reports_directory': str(REPORTS_DIR)
        }
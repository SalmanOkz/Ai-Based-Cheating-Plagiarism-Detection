"""
Unified Risk Scoring System
Single source of truth for risk calculation across all modules
"""
from typing import Dict, Tuple, List
from dataclasses import dataclass

@dataclass
class RiskWeights:
    """Risk weight configuration"""
    # Gaze tracking weights
    GAZE_CRITICAL = 4.0      # Looking down, severe deviation
    GAZE_WARNING = 2.0       # Moderate deviation
    GAZE_NORMAL = 0.0        # Looking at screen
    
    # Person count weights
    NO_PERSON = 5.0          # Student disappeared
    MULTIPLE_PERSONS = 4.0   # Multiple students detected
    SINGLE_PERSON = 0.0      # Normal - one student
    
    # Prohibited items weights
    PHONE_DETECTED = 3.0     # Mobile phone
    BOOK_DETECTED = 2.5      # Books/notes
    OTHER_PROHIBITED = 2.0   # Other suspicious items
    
    # Activity weights
    SUSPICIOUS_ACTIVITY = 1.0  # Per suspicious activity
    
    # Maximum risk score
    MAX_RISK = 10.0

class RiskCalculator:
    """Unified risk calculator for all modules"""
    
    def __init__(self, weights: RiskWeights = None):
        self.weights = weights or RiskWeights()
    
    def calculate_risk(self, 
                      gaze_level: int = 0,
                      person_count: int = 1,
                      prohibited_items: List[Dict] = None,
                      suspicious_activities: List[str] = None,
                      max_students: int = 1) -> float:
        """
        Calculate unified risk score
        
        Args:
            gaze_level: 0=normal, 1=warning, 2=critical
            person_count: Number of persons detected
            prohibited_items: List of prohibited item detections
            suspicious_activities: List of suspicious activity strings
            max_students: Maximum allowed students (default 1)
        
        Returns:
            Risk score (0-10)
        """
        risk = 0.0
        
        # Gaze risk
        if gaze_level == 2:
            risk += self.weights.GAZE_CRITICAL
        elif gaze_level == 1:
            risk += self.weights.GAZE_WARNING
        
        # Person count risk
        if person_count == 0:
            risk += self.weights.NO_PERSON
        elif person_count > max_students:
            # Risk increases with number of extra persons
            extra_persons = person_count - max_students
            risk += self.weights.MULTIPLE_PERSONS + (extra_persons - 1) * 0.5
        
        # Prohibited items risk
        if prohibited_items:
            for item in prohibited_items:
                item_name = item.get('item', '').lower() if isinstance(item, dict) else str(item).lower()
                
                if 'phone' in item_name or 'cell' in item_name:
                    risk += self.weights.PHONE_DETECTED
                elif 'book' in item_name:
                    risk += self.weights.BOOK_DETECTED
                else:
                    risk += self.weights.OTHER_PROHIBITED
        
        # Suspicious activities risk
        if suspicious_activities:
            risk += len(suspicious_activities) * self.weights.SUSPICIOUS_ACTIVITY
        
        # Cap at maximum
        return min(self.weights.MAX_RISK, risk)
    
    def determine_alert_level(self, risk_score: float) -> Tuple[str, bool]:
        """
        Determine alert level from risk score
        
        Args:
            risk_score: Risk score (0-10)
        
        Returns:
            Tuple of (alert_level, is_cheating)
        """
        if risk_score >= 6.0:
            return 'CRITICAL', True
        elif risk_score >= 3.0:
            return 'WARNING', False
        else:
            return 'NORMAL', False
    
    def calculate_from_results(self, results: Dict, max_students: int = 1) -> Dict:
        """
        Calculate risk from detection results dictionary
        
        Args:
            results: Detection results from any module
            max_students: Maximum allowed students
        
        Returns:
            Dict with risk_score, alert_level, is_cheating
        """
        # Extract gaze level
        gaze_level = 0
        gaze_analysis = results.get('gaze_analysis', {})
        if gaze_analysis:
            gaze_level = gaze_analysis.get('level', 0)
        
        # Extract person count
        person_count = results.get('person_count', 1)
        
        # Extract prohibited items
        prohibited_items = []
        
        # Check in different possible locations
        if 'prohibited_items' in results:
            prohibited_items = results['prohibited_items']
        elif 'object_analysis' in results and results['object_analysis']:
            prohibited_items = results['object_analysis'].get('prohibited_items', [])
        
        # Also check detections
        if 'detections' in results:
            for det in results['detections']:
                if isinstance(det, dict) and det.get('is_prohibited', False):
                    prohibited_items.append({
                        'item': det.get('class_name', 'unknown'),
                        'confidence': det.get('confidence', 0)
                    })
        
        # Extract suspicious activities
        suspicious_activities = results.get('suspicious_activities', [])
        
        # Calculate risk
        risk_score = self.calculate_risk(
            gaze_level=gaze_level,
            person_count=person_count,
            prohibited_items=prohibited_items,
            suspicious_activities=suspicious_activities,
            max_students=max_students
        )
        
        # Determine alert level
        alert_level, is_cheating = self.determine_alert_level(risk_score)
        
        return {
            'risk_score': round(risk_score, 1),
            'alert_level': alert_level,
            'is_cheating': is_cheating,
            'risk_breakdown': {
                'gaze_level': gaze_level,
                'person_count': person_count,
                'prohibited_items_count': len(prohibited_items),
                'suspicious_activities_count': len(suspicious_activities)
            }
        }
    
    def get_risk_explanation(self, risk_score: float) -> str:
        """Get human-readable explanation of risk level"""
        if risk_score >= 8.0:
            return "SEVERE: Multiple critical violations detected"
        elif risk_score >= 6.0:
            return "HIGH: Critical violation detected, immediate review required"
        elif risk_score >= 4.0:
            return "MODERATE: Suspicious behavior detected, monitor closely"
        elif risk_score >= 2.0:
            return "LOW: Minor concerns detected"
        else:
            return "NORMAL: No significant concerns"


# Global instance
_global_calculator = RiskCalculator()

def calculate_risk(**kwargs) -> float:
    """Global function for risk calculation"""
    return _global_calculator.calculate_risk(**kwargs)

def determine_alert_level(risk_score: float) -> Tuple[str, bool]:
    """Global function for alert level determination"""
    return _global_calculator.determine_alert_level(risk_score)

def calculate_from_results(results: Dict, max_students: int = 1) -> Dict:
    """Global function to calculate risk from results"""
    return _global_calculator.calculate_from_results(results, max_students)
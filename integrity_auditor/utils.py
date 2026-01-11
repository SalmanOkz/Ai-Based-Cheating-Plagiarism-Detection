"""
Utility functions for integrity auditor
"""
import json
import datetime
import os
import hashlib
from typing import Any, Dict, Optional


def generate_report_id() -> str:
    """Generate unique report ID"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"REPORT_{timestamp}"


def save_analysis_result(result: Dict, filename: Optional[str] = None) -> str:
    """Save analysis result to JSON file"""
    if filename is None:
        filename = f"analysis_{generate_report_id()}.json"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return filename


def calculate_text_hash(text: str) -> str:
    """Calculate MD5 hash of text"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def format_percentage(value: float) -> str:
    """Format percentage with 2 decimal places"""
    return f"{value:.2f}%"


def ensure_directory(directory_path: str) -> None:
    """Ensure a directory exists, create if not"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return os.path.splitext(filename)[1].lower()


def read_file_content(filepath: str) -> str:
    """Read file content with proper encoding handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()


def write_file_content(filepath: str, content: str) -> None:
    """Write content to file with UTF-8 encoding"""
    ensure_directory(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


class IntegrityLogger:
    """Logs integrity audit activities"""
    
    def __init__(self, log_file: str = "./logs/integrity_audits.log"):
        self.log_file = log_file
        ensure_directory(os.path.dirname(log_file))
    
    def log_audit(self, action: str, result: Dict, user: str = "system") -> None:
        """Log an audit action"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user,
            "action": action,
            "result": result
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def get_recent_logs(self, limit: int = 10) -> list:
        """Get recent audit logs"""
        if not os.path.exists(self.log_file):
            return []
        
        logs = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get last 'limit' lines
        for line in lines[-limit:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
        
        return logs


def get_file_size(filepath: str) -> str:
    """Get human readable file size"""
    if not os.path.exists(filepath):
        return "0 B"
    
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def clean_temp_files(temp_dir: str = "/tmp/integrity_auditor", max_age_hours: int = 24) -> None:
    """Clean temporary files older than specified hours"""
    if not os.path.exists(temp_dir):
        return
    
    current_time = datetime.datetime.now().timestamp()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        try:
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                os.remove(filepath)
        except (OSError, FileNotFoundError):
            continue


def create_temp_file(content: str = "", extension: str = ".txt") -> str:
    """Create a temporary file with given content and return its path"""
    import tempfile
    
    temp_dir = "/tmp/integrity_auditor"
    ensure_directory(temp_dir)
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=temp_dir,
        suffix=extension,
        delete=False,
        encoding='utf-8'
    ) as f:
        if content:
            f.write(content)
        return f.name


def validate_file_path(filepath: str) -> tuple[bool, str]:
    """Validate if file path exists and is accessible"""
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    if not os.path.isfile(filepath):
        return False, f"Path is not a file: {filepath}"
    
    if not os.access(filepath, os.R_OK):
        return False, f"No read permission for file: {filepath}"
    
    return True, "Valid"


def get_project_root() -> str:
    """Get project root directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from integrity_auditor module
    return os.path.dirname(current_dir)


def get_config_path() -> str:
    """Get configuration file path"""
    project_root = get_project_root()
    config_path = os.path.join(project_root, "config", "integrity_config.json")
    
    # Create default config if doesn't exist
    if not os.path.exists(config_path):
        default_config = {
            "model_paths": {
                "ai_detector": "./models/ai_detector",
                "stylometry": "./models/stylometry_model.pkl"
            },
            "thresholds": {
                "plagiarism": 75,
                "ai_detection": 50
            },
            "logging": {
                "enabled": True,
                "level": "INFO"
            }
        }
        ensure_directory(os.path.dirname(config_path))
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    return config_path


def load_config() -> Dict:
    """Load configuration from file"""
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        return json.load(f)


def save_config(config: Dict) -> None:
    """Save configuration to file"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    # Test the utilities
    print("Testing utilities...")
    
    # Test report ID generation
    report_id = generate_report_id()
    print(f"Report ID: {report_id}")
    
    # Test text hash
    hash_val = calculate_text_hash("Hello World")
    print(f"Text hash: {hash_val}")
    
    # Test percentage formatting
    print(f"Formatted percentage: {format_percentage(85.1234)}")
    
    # Test directory creation
    test_dir = "./test_directory"
    ensure_directory(test_dir)
    print(f"Directory created/exists: {os.path.exists(test_dir)}")
    
    # Clean up
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    print("Utilities test completed!")
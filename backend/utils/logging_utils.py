"""
Logging utilities with UTF-8 support for Windows
"""
import logging
import sys
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    """Get logger with UTF-8 encoding support for Windows"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        
        # FIX: Force UTF-8 encoding for Windows
        if hasattr(handler.stream, 'reconfigure'):
            try:
                handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO):
    """Setup logging configuration"""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path / "vision_guardian.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Fix stream encoding for Windows
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            if hasattr(handler.stream, 'reconfigure'):
                try:
                    handler.stream.reconfigure(encoding='utf-8', errors='replace')
                except:
                    pass
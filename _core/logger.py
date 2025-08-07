import logging
import sys
from pathlib import Path
from .config import config


def setup_logging():
    """Setup logging configuration for both file and console output."""
    
    # Create logs directory if it doesn't exist
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Setup root logger
    logging.basicConfig(
        level=config.log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # File handler
            logging.FileHandler(log_path / config["logging"]["log_file"], encoding='utf-8'),
            # Console handler
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


# Initialize logging when module is imported
setup_logging()

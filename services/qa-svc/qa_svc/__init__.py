"""
QA module initialization.
Sets up logging for the entire QA system.
"""
import logging
import sys

# Configure logging for QA module
def setup_qa_logging():
    """Setup logging configuration for QA module."""
    # Get QA logger
    qa_logger = logging.getLogger('qa_svc')
    qa_logger.setLevel(logging.INFO)
    
    # Create console handler if not exists
    if not qa_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        qa_logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    qa_logger.propagate = False
    
    return qa_logger

# Setup logging when module is imported
setup_qa_logging()


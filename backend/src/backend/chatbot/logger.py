"""
Logging configuration for chatbot system.
"""

import logging
import sys
from datetime import datetime

# Create logger
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)

# Create console handler with formatting
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


handler.setFormatter(formatter)
logger.addHandler(handler)

# Prevent duplicate handlers
if len(logger.handlers) > 1:
    logger.handlers = [logger.handlers[0]]


"""
CyborgDB Manager - Wrapper for Lite (Embedded) SDK
Uses the same approach as the working project with embedded cyborgdb library
"""

import os
import logging
from backend.cyborg_lite_manager import CyborgLiteManager

logger = logging.getLogger(__name__)

def get_cyborg_manager():
    """Get CyborgDB Lite manager instance"""
    try:
        manager = CyborgLiteManager()
        return manager
    except Exception as e:
        logger.error(f"Failed to initialize CyborgDB: {e}")
        raise

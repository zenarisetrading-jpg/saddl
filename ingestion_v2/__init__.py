"""
Ingestion V2 Module
===================
New ingestion infrastructure for Saddle AdPulse.
PRD Reference: EMAIL_INGESTION_PRD.md

This module is ISOLATED from the V1 codebase.
No imports from or modifications to existing code.
"""

__version__ = "0.1.0"
__all__ = [
    "IngestionSource",
    "IngestionStatus", 
    "IngestionPayload",
    "IngestionEvent",
    "BaseAdapter",
    "BaseValidator",
    "BaseStorage",
    "BaseParser",
]

from .enums import IngestionSource, IngestionStatus
from .models import IngestionPayload, IngestionEvent
from .interfaces import BaseAdapter, BaseValidator, BaseStorage, BaseParser

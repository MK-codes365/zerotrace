"""
ZEROTrace — Structured JSON Logging
All log entries include case_id, job_id, worker_id where applicable.
"""

import logging
import sys
from datetime import datetime, timezone

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

from app.core.config import settings


def setup_logging():
    """Configure structured JSON logging for the application."""
    if HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                (
                    structlog.dev.ConsoleRenderer()
                    if getattr(settings, "LOG_FORMAT", "json") != "json"
                    else structlog.processors.JSONRenderer()
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, getattr(settings, "LOG_LEVEL", "INFO").upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )
    else:
        logging.basicConfig(
            level=getattr(logging, getattr(settings, "LOG_LEVEL", "INFO").upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            stream=sys.stdout,
        )


def get_logger(name: str = "zerotrace"):
    """Get a structured logger instance."""
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    return logging.getLogger(name)


def forensic_log(
    event: str,
    *,
    case_id: str = None,
    job_id: str = None,
    worker_id: str = None,
    evidence_id: str = None,
    operator: str = None,
    level: str = "info",
    **kwargs,
):
    """
    Create a forensic-grade log entry.
    These entries are structured for audit trail compliance.
    """
    logger = get_logger("forensic")
    log_fn = getattr(logger, level, logger.info)
    log_fn(
        event,
        case_id=case_id,
        job_id=job_id,
        worker_id=worker_id,
        evidence_id=evidence_id,
        operator=operator,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **kwargs,
    )

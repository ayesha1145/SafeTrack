# ============================================================
# SafeTrack Monitoring Module
# ------------------------------------------------------------
# Sends telemetry to Azure Application Insights: request timing,
# errors, and key safety-critical business events (alerts created,
# SOS triggered, resolution times). This gives visibility into how
# the deployed app is actually behaving — not just whether it's up,
# but how it's performing and where it's failing.
#
# Design notes:
# - Fails soft: if Application Insights isn't configured, or a call
#   to it errors, we log locally and move on. Telemetry must never
#   block or fail the request it's describing.
# - Kept as its own module so server.py stays focused on routing.
# ============================================================

import os
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

APPINSIGHTS_CONNECTION_STRING = os.environ.get("APPINSIGHTS_CONNECTION_STRING")
MONITORING_ENABLED = bool(APPINSIGHTS_CONNECTION_STRING)

_azure_logger = None
_azure_exporter = None

if MONITORING_ENABLED:
    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        from opencensus.ext.azure import metrics_exporter

        _azure_logger = logging.getLogger("safetrack.telemetry")
        _azure_logger.addHandler(AzureLogHandler(connection_string=APPINSIGHTS_CONNECTION_STRING))
        _azure_logger.setLevel(logging.INFO)
        logger.info("Azure Application Insights monitoring enabled")
    except Exception as e:
        logger.error(f"Failed to initialize Application Insights: {e}")
        MONITORING_ENABLED = False
else:
    logger.warning(
        "APPINSIGHTS_CONNECTION_STRING not set — telemetry is disabled. "
        "App will run normally without monitoring."
    )


def track_event(name: str, properties: dict = None) -> None:
    """Record a named business event (e.g. 'alert_created', 'sos_triggered')
    with optional structured properties. Never raises."""
    if not MONITORING_ENABLED or _azure_logger is None:
        return
    try:
        _azure_logger.info(name, extra={"custom_dimensions": properties or {}})
    except Exception as e:
        logger.error(f"Failed to send telemetry event '{name}': {e}")


def track_exception(exc: Exception, context: str = "") -> None:
    """Record an unhandled or notable exception, with optional context
    about where it happened. Never raises."""
    if not MONITORING_ENABLED or _azure_logger is None:
        return
    try:
        _azure_logger.exception(f"{context}: {exc}" if context else str(exc))
    except Exception as e:
        logger.error(f"Failed to send exception telemetry: {e}")


@contextmanager
def track_duration(operation_name: str):
    """Context manager that times a block of code and logs it as an event
    with the elapsed milliseconds. Usage:
        with track_duration('create_alert'):
            ... do work ...
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        track_event(f"{operation_name}_duration", {"duration_ms": elapsed_ms})

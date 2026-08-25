# ============================================================
# SafeTrack Photo Storage Module
# ------------------------------------------------------------
# Uploads photos attached to emergency alerts to Azure Blob
# Storage, and returns a public URL to store alongside the alert
# record. Lets a student attach photo evidence (an injury, a
# hazard, the scene) when reporting an emergency.
#
# Design notes:
# - Fails soft on the SAME pattern as everything else: if storage
#   isn't configured or the upload fails, the alert itself still
#   gets created — a photo upload failure must never block a
#   safety-critical alert from going through.
# - Validates file type and size before upload to avoid abuse.
# ============================================================

import os
import logging
import uuid

logger = logging.getLogger(__name__)

AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER", "alert-photos")

STORAGE_ENABLED = bool(AZURE_STORAGE_CONNECTION_STRING)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

if not STORAGE_ENABLED:
    logger.warning(
        "AZURE_STORAGE_CONNECTION_STRING not set — photo uploads are disabled. "
        "Alerts can still be created without a photo."
    )


async def upload_alert_photo(file_bytes: bytes, content_type: str, alert_id: str) -> str | None:
    """Uploads a photo to Azure Blob Storage and returns its public URL,
    or None if storage isn't configured or the upload fails. Never raises —
    callers should treat a None return as 'no photo attached', not an error."""
    if not STORAGE_ENABLED:
        logger.info("Photo upload skipped: storage not configured")
        return None

    if content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(f"Rejected photo upload: unsupported content type '{content_type}'")
        return None

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Rejected photo upload: file too large ({len(file_bytes)} bytes)")
        return None

    try:
        from azure.storage.blob.aio import BlobServiceClient

        extension = content_type.split("/")[-1]
        blob_name = f"{alert_id}/{uuid.uuid4()}.{extension}"

        async with BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        ) as blob_service_client:
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(
                file_bytes, overwrite=True, content_settings=None
            )
            return blob_client.url
    except Exception as e:
        logger.error(f"Failed to upload alert photo: {e}")
        return None

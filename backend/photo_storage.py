# ============================================================
# SafeTrack Photo Storage Module
# ------------------------------------------------------------
# Uploads photos attached to emergency alerts to Azure Blob
# Storage, and returns a secure, time-limited URL to store
# alongside the alert record. Lets a student attach photo
# evidence (an injury, a hazard, the scene) when reporting an
# emergency.
#
# Design notes:
# - The storage account's anonymous public access is disabled
#   (org policy), so instead of a plain public blob URL, each
#   photo gets a SAS (Shared Access Signature) token appended —
#   a secure, expiring link that only someone with the exact URL
#   can use. This is the standard, more secure pattern anyway.
# - Fails soft on the SAME pattern as everything else: if storage
#   isn't configured or the upload fails, the alert itself still
#   gets created — a photo upload failure must never block a
#   safety-critical alert from going through.
# - Validates file type and size before upload to avoid abuse.
# ============================================================

import os
import logging
import uuid
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("AZURE_STORAGE_CONTAINER", "alert-photos")
SAS_EXPIRY_DAYS = int(os.environ.get("AZURE_STORAGE_SAS_EXPIRY_DAYS", "365"))

STORAGE_ENABLED = bool(AZURE_STORAGE_CONNECTION_STRING)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

if not STORAGE_ENABLED:
    logger.warning(
        "AZURE_STORAGE_CONNECTION_STRING not set — photo uploads are disabled. "
        "Alerts can still be created without a photo."
    )


def _parse_connection_string(conn_str: str) -> dict:
    """Extract account name/key from a standard Azure connection string."""
    parts = dict(
        item.split("=", 1) for item in conn_str.split(";") if "=" in item
    )
    return parts


async def upload_alert_photo(file_bytes: bytes, content_type: str, alert_id: str) -> str | None:
    """Uploads a photo to Azure Blob Storage and returns a secure, time-limited
    URL (SAS token), or None if storage isn't configured or the upload fails.
    Never raises — callers should treat a None return as 'no photo attached',
    not an error."""
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
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions

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

            conn_parts = _parse_connection_string(AZURE_STORAGE_CONNECTION_STRING)
            sas_token = generate_blob_sas(
                account_name=conn_parts["AccountName"],
                container_name=CONTAINER_NAME,
                blob_name=blob_name,
                account_key=conn_parts["AccountKey"],
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(days=SAS_EXPIRY_DAYS),
            )
            return f"{blob_client.url}?{sas_token}"
    except Exception as e:
        logger.error(f"Failed to upload alert photo: {e}")
        return None

from datetime import datetime

from config import APP_VERSION


def build_metadata(backup_mode, selected_categories, user_id=None, output_dir=None, extra=None):
    current = datetime.now().astimezone()
    metadata = {
        "app_version": APP_VERSION,
        "backup_mode": backup_mode,
        "generated_at": current.isoformat(),
        "timezone": current.tzname() or str(current.tzinfo),
        "selected_categories": list(selected_categories or []),
    }

    if user_id:
        metadata["user_id"] = user_id

    if output_dir:
        metadata["output_dir"] = output_dir

    if extra:
        metadata.update(extra)

    return metadata


def merge_metadata(base_metadata=None, override_metadata=None):
    metadata = dict(base_metadata or {})
    if override_metadata:
        metadata.update(override_metadata)

    current = datetime.now().astimezone()
    metadata.setdefault("app_version", APP_VERSION)
    metadata.setdefault("generated_at", current.isoformat())
    metadata.setdefault("timezone", current.tzname() or str(current.tzinfo))
    metadata.setdefault("selected_categories", [])
    return metadata


def metadata_rows(metadata):
    rows = []
    for key, value in merge_metadata(metadata).items():
        if isinstance(value, list):
            value = ",".join(str(item) for item in value)
        rows.append((key, value))
    return rows

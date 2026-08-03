import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from app.cache.cache import CacheManager
from app.processor.canonical import canonical_name
from app.processor.hash import calculate_hash
from app.processor.image import process_image
from app.source import SourceError, load_menu
from app.storage import create_storage


def get_enabled_storages(config):
    storages = []
    for name, storage_config in config.get("storage", {}).items():
        if not storage_config.get("enabled", False):
            continue
        try:
            storages.append((name, create_storage(name, storage_config)))
        except (KeyError, ValueError) as exc:
            print(f"[ERROR] Storage {name} is unavailable: {exc}", flush=True)
    return storages


def now():
    return datetime.now(timezone.utc).isoformat()


def set_item(cache, key, **values):
    item = cache.get(key) or {}
    item.update(values)
    item["updated_at"] = now()
    cache.set(key, item)
    cache.save()


def download(url, destination, timeout):
    request = Request(url, headers={"User-Agent": "vinvinvin-image-processor/1.0"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310 - menu URL is operator content
        with destination.open("wb") as output:
            shutil.copyfileobj(response, output)


def process_images(config):
    print("Image processing started", flush=True)
    cache = CacheManager()
    storages = get_enabled_storages(config)
    if not storages:
        print("[ERROR] No enabled storage found", flush=True)
        return

    try:
        menu = load_menu(config)
    except SourceError as exc:
        print(f"[ERROR] {exc}", flush=True)
        return

    timeout = config.get("source", {}).get("timeout_seconds", 30)
    for item in menu:
        key = canonical_name(item.category, item.name)
        if not item.is_url:
            if item.is_local_webp:
                set_item(
                    cache,
                    key,
                    category=item.category,
                    name=item.name,
                    source=item.photo,
                    source_type="local",
                    status="skipped",
                    reason="local_webp"
                )
                continue
            set_item(
                cache,
                key,
                category=item.category,
                name=item.name,
                source=item.photo,
                source_type="local",
                status="error",
                error="Local non-WebP image cannot be fetched."
            )
            continue

        try:
            with tempfile.TemporaryDirectory(prefix="image-processor-") as temp_dir:
                source = Path(temp_dir) / "source"
                download(item.photo, source, timeout)
                source_hash = calculate_hash(source)
                output = process_image(source, item.category, Path(temp_dir), key)
                destination = output.name
                storage_status = {}
                for storage_name, storage in storages:
                    previous = (cache.get(key) or {}).get("storage", {}).get(storage_name, {})
                    if previous.get("status") == "success" and previous.get("source_hash") == source_hash and previous.get("destination") == destination and storage.exists(destination):
                        storage_status[storage_name] = previous
                        continue
                    try:
                        storage.upload(output, destination)
                        storage_status[storage_name] = {"status": "success", "destination": destination, "source_hash": source_hash, "updated_at": now()}
                    except Exception as exc:
                        storage_status[storage_name] = {"status": "error", "destination": destination, "source_hash": source_hash, "error": str(exc), "updated_at": now()}
                failed = [name for name, status in storage_status.items() if status["status"] == "error"]
                set_item(
                    cache,
                    key,
                    category=item.category,
                    name=item.name,
                    source=item.photo,
                    source_type="url",
                    source_hash=source_hash,
                    destination=destination,
                    status="error" if failed else "success",
                    error=f"Upload failed: {', '.join(failed)}" if failed else None,
                    storage=storage_status
                )
        except Exception as exc:
            set_item(
                cache,
                key,
                category=item.category,
                name=item.name,
                source=item.photo,
                source_type="url",
                status="error",
                error=str(exc)
            )

    print("Image processing finished", flush=True)


import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from app.cache.cache import CacheManager
from app.processor.hash import calculate_hash, calculate_menu_hash
from app.processor.image import process_image
from app.source import SourceError, load_menu
from app.storage import create_storage


CATEGORY_MAP = {
    "레드": "Red",
    "화이트": "White",
    "로제": "Rose",
    "스파클링": "Sparkling",
    "샴페인": "Champagne",
    "안주": "Snack",
    "글라스 와인": "Glass",
}


def get_category_prefix(category):
    return CATEGORY_MAP.get(
        category,
        "Other"
    )


def get_enabled_storages(config):
    storages = []

    for name, storage_config in config.get(
        "storage",
        {}
    ).items():

        if not storage_config.get(
            "enabled",
            False
        ):
            continue

        try:
            storage = create_storage(
                name,
                storage_config
            )

            storages.append(
                (
                    name,
                    storage
                )
            )

        except (
            KeyError,
            ValueError
        ) as exc:

            print(
                f"[ERROR] Storage {name} is unavailable: {exc}",
                flush=True
            )

    return storages


def now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def set_item(
    cache,
    key,
    **values
):
    item = cache.get(
        key
    ) or {}

    item.update(
        values
    )

    item["updated_at"] = now()

    cache.set(
        key,
        item
    )

    cache.save()


def download(
    url,
    destination,
    timeout
):
    request = Request(
        url,
        headers={
            "User-Agent":
                "vinvinvin-image-processor/1.0"
        }
    )

    with urlopen(
        request,
        timeout=timeout
    ) as response:

        with destination.open(
            "wb"
        ) as output:

            shutil.copyfileobj(
                response,
                output
            )


def process_images(config):
    print(
        "Image processing started",
        flush=True
    )

    cache = CacheManager()

    storages = get_enabled_storages(
        config
    )

    if not storages:
        print(
            "[ERROR] No enabled storage found",
            flush=True
        )
        return

    try:
        menu = load_menu(
            config
        )

    except SourceError as exc:
        print(
            f"[ERROR] {exc}",
            flush=True
        )
        return

    timeout = config.get(
        "source",
        {}
    ).get(
        "timeout_seconds",
        30
    )

    current_keys = set()

    for item in menu:

        menu_hash = calculate_menu_hash(
            item.category,
            item.name
        )

        current_keys.add(
            menu_hash
        )

        if not item.is_url:

            if item.is_local_webp:
                set_item(
                    cache,
                    menu_hash,
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
                menu_hash,
                category=item.category,
                name=item.name,
                source=item.photo,
                source_type="local",
                status="error",
                error="Local non-WebP image cannot be fetched."
            )
            continue

        try:

            with tempfile.TemporaryDirectory(
                prefix="image-processor-"
            ) as temp_dir:

                temp_dir = Path(
                    temp_dir
                )

                source = (
                    temp_dir /
                    "source"
                )

                download(
                    item.photo,
                    source,
                    timeout
                )

                image_hash = calculate_hash(
                    source
                )

                filename = (
                    f"{get_category_prefix(item.category)}_"
                    f"{image_hash[:16]}.webp"
                )

                output = process_image(
                    source,
                    item.category,
                    temp_dir,
                    filename
                )

                storage_status = {}

                previous_item = (
                    cache.get(
                        menu_hash
                    ) or {}
                )

                previous_storages = (
                    previous_item.get(
                        "storage",
                        {}
                    )
                )

                for (
                    storage_name,
                    storage
                ) in storages:

                    previous = (
                        previous_storages.get(
                            storage_name,
                            {}
                        )
                    )

                    if (
                        previous.get(
                            "status"
                        ) == "success"
                        and previous.get(
                            "image_hash"
                        ) == image_hash
                        and previous.get(
                            "destination"
                        ) == filename
                        and storage.exists(
                            filename
                        )
                    ):
                        storage_status[
                            storage_name
                        ] = previous

                        continue

                    try:

                        old_destination = previous.get(
                            "destination"
                        )

                        if (
                            old_destination
                            and old_destination != filename
                            and storage.exists(
                                old_destination
                            )
                        ):
                            storage.delete(
                                old_destination
                            )

                            print(
                                "[INFO] Replaced old image: "
                                f"{storage_name}/{old_destination}",
                                flush=True
                            )

                        storage.upload(
                            output,
                            filename
                        )

                        storage_status[
                            storage_name
                        ] = {
                            "status": "success",
                            "destination": filename,
                            "image_hash": image_hash,
                            "updated_at": now()
                        }

                    except Exception as exc:

                        storage_status[
                            storage_name
                        ] = {
                            "status": "error",
                            "destination": filename,
                            "image_hash": image_hash,
                            "error": str(exc),
                            "updated_at": now()
                        }

                failed = [
                    name
                    for (
                        name,
                        status
                    ) in storage_status.items()
                    if status.get(
                        "status"
                    ) == "error"
                ]

                set_item(
                    cache,
                    menu_hash,
                    category=item.category,
                    name=item.name,
                    source=item.photo,
                    source_type="url",
                    image_hash=image_hash,
                    destination=filename,
                    status=(
                        "error"
                        if failed
                        else "success"
                    ),
                    error=(
                        f"Upload failed: {', '.join(failed)}"
                        if failed
                        else None
                    ),
                    storage=storage_status
                )

        except Exception as exc:

            set_item(
                cache,
                menu_hash,
                category=item.category,
                name=item.name,
                source=item.photo,
                source_type="url",
                status="error",
                error=str(exc)
            )

    # 현재 메뉴에서 사라진 항목 처리
    stale_keys = (
        cache.keys()
        - current_keys
    )

    for key in stale_keys:

        item = cache.get(
            key
        ) or {}

        storage_status = item.get(
            "storage",
            {}
        )

        for (
            storage_name,
            storage
        ) in storages:

            previous = (
                storage_status.get(
                    storage_name,
                    {}
                )
            )

            destination = (
                previous.get(
                    "destination"
                )
                or item.get(
                    "destination"
                )
            )

            if not destination:
                continue

            try:

                if storage.exists(
                    destination
                ):

                    storage.delete(
                        destination
                    )

                    print(
                        "[INFO] Deleted stale image: "
                        f"{storage_name}/{destination}",
                        flush=True
                    )

            except Exception as exc:

                print(
                    "[ERROR] Failed to delete stale image "
                    f"{storage_name}/{destination}: {exc}",
                    flush=True
                )

        cache.remove(
            key
        )

    cache.save()

    print(
        "Image processing finished",
        flush=True
    )
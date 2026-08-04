from datetime import datetime, timezone

from app.cache.cache import CacheManager
from app.processor.operation import (
    DeleteOperation,
    UploadOperation,
)


def now():
    return datetime.now(
        timezone.utc
    ).isoformat()


class SyncEngine:

    def __init__(self, storages):
        self.cache = CacheManager()
        self.storages = storages

    def get_cached_item(self, key):
        return self.cache.get(key)

    def find_by_source(
        self,
        source,
        category
    ):
        for key in self.cache.keys():

            item = self.cache.get(key)

            if not item:
                continue

            if item.get("source") != source:
                continue

            if item.get("category") != category:
                continue

            if item.get("status") != "success":
                continue

            image_hash = item.get("image_hash")
            destination = item.get("destination")

            if not image_hash or not destination:
                continue

            return key, item

        return None, None

    def _save_item(
        self,
        key,
        item
    ):
        item["updated_at"] = now()

        self.cache.set(
            key,
            item
        )

        self.cache.save()

    def skip_item(
        self,
        key,
        category,
        name,
        source,
        cached_item
    ):
        item = dict(cached_item)

        item.update({
            "category": category,
            "name": name,
            "source": source,
            "updated_at": now()
        })

        self.cache.set(
            key,
            item
        )

        self.cache.save()

        return item

    def reuse_item(
        self,
        key,
        category,
        name,
        source,
        image_hash,
        filename,
        source_key
    ):
        source_item = (
            self.cache.get(source_key)
            or {}
        )

        source_storages = source_item.get(
            "storage",
            {}
        )

        storage_status = {}

        for storage_name, storage in self.storages:

            source_status = (
                source_storages.get(
                    storage_name,
                    {}
                )
            )

            if (
                source_status.get("status") == "success"
                and source_status.get("destination") == filename
                and storage.exists(filename)
            ):
                storage_status[storage_name] = {
                    "status": "success",
                    "destination": filename,
                    "image_hash": image_hash,
                    "updated_at": now()
                }

                continue

            if storage.exists(filename):
                storage_status[storage_name] = {
                    "status": "success",
                    "destination": filename,
                    "image_hash": image_hash,
                    "updated_at": now()
                }

                continue

            storage_status[storage_name] = {
                "status": "error",
                "destination": filename,
                "image_hash": image_hash,
                "error": (
                    "Existing cached image is not present "
                    f"in storage '{storage_name}'."
                ),
                "updated_at": now()
            }

        return self._set_synced_item(
            key=key,
            category=category,
            name=name,
            source=source,
            image_hash=image_hash,
            filename=filename,
            storage_status=storage_status
        )

    def _set_synced_item(
        self,
        key,
        category,
        name,
        source,
        image_hash,
        filename,
        storage_status
    ):
        failed = [
            storage_name
            for storage_name, status
            in storage_status.items()
            if status.get("status") == "error"
        ]

        item = {
            "category": category,
            "name": name,
            "source": source,
            "source_type": "url",
            "image_hash": image_hash,
            "destination": filename,
            "status": (
                "error"
                if failed
                else "success"
            ),
            "error": (
                f"Storage failed: {', '.join(failed)}"
                if failed
                else None
            ),
            "storage": storage_status,
            "updated_at": now()
        }

        self.cache.set(
            key,
            item
        )

        self.cache.save()

        return item

    def build_upload_operations(
        self,
        key,
        filename,
        output
    ):
        return [
            UploadOperation(
                key=key,
                source=output,
                destination=filename
            )
        ]

    def build_delete_operation(
        self,
        key,
        destination
    ):
        return DeleteOperation(
            key=key,
            destination=destination
        )

    def execute_upload(
        self,
        operation,
        previous_item,
        image_hash
    ):
        previous_storages = (
            previous_item.get(
                "storage",
                {}
            )
        )

        storage_status = {}

        for storage_name, storage in self.storages:

            previous = (
                previous_storages.get(
                    storage_name,
                    {}
                )
            )

            previous_destination = (
                previous.get(
                    "destination"
                )
            )

            previous_hash = (
                previous.get(
                    "image_hash"
                )
            )

            if (
                previous.get("status") == "success"
                and previous_hash == image_hash
                and previous_destination == operation.destination
                and storage.exists(
                    operation.destination
                )
            ):
                storage_status[storage_name] = previous
                continue

            try:

                if (
                    previous_destination
                    and previous_destination != operation.destination
                    and storage.exists(
                        previous_destination
                    )
                ):
                    storage.delete(
                        previous_destination
                    )

                    print(
                        "[INFO] Replaced old image: "
                        f"{storage_name}/{previous_destination}",
                        flush=True
                    )

                storage.upload(
                    operation.source,
                    operation.destination
                )

                storage_status[storage_name] = {
                    "status": "success",
                    "destination": operation.destination,
                    "image_hash": image_hash,
                    "updated_at": now()
                }

            except Exception as exc:

                storage_status[storage_name] = {
                    "status": "error",
                    "destination": operation.destination,
                    "image_hash": image_hash,
                    "error": str(exc),
                    "updated_at": now()
                }

        return storage_status

    def sync_item(
        self,
        key,
        category,
        name,
        source,
        image_hash,
        filename,
        output
    ):
        previous_item = (
            self.cache.get(key)
            or {}
        )

        operation = UploadOperation(
            key=key,
            source=output,
            destination=filename
        )

        storage_status = self.execute_upload(
            operation=operation,
            previous_item=previous_item,
            image_hash=image_hash
        )

        return self._set_synced_item(
            key=key,
            category=category,
            name=name,
            source=source,
            image_hash=image_hash,
            filename=filename,
            storage_status=storage_status
        )

    def execute_delete(
        self,
        operation
    ):
        for storage_name, storage in self.storages:

            try:

                if not storage.exists(
                    operation.destination
                ):
                    continue

                storage.delete(
                    operation.destination
                )

                print(
                    "[INFO] Deleted stale image: "
                    f"{storage_name}/{operation.destination}",
                    flush=True
                )

            except Exception as exc:

                print(
                    "[ERROR] Failed to delete stale image "
                    f"{storage_name}/{operation.destination}: {exc}",
                    flush=True
                )

    def remove_stale_items(
        self,
        current_keys
    ):
        stale_keys = (
            self.cache.keys()
            - current_keys
        )

        active_destinations = set()

        for key in current_keys:

            item = self.cache.get(key)

            if not item:
                continue

            destination = item.get(
                "destination"
            )

            if destination:
                active_destinations.add(
                    destination
                )

        for key in stale_keys:

            item = (
                self.cache.get(key)
                or {}
            )

            storage_status = item.get(
                "storage",
                {}
            )

            destinations = set()

            item_destination = item.get(
                "destination"
            )

            if item_destination:
                destinations.add(
                    item_destination
                )

            for status in storage_status.values():

                destination = status.get(
                    "destination"
                )

                if destination:
                    destinations.add(
                        destination
                    )

            for destination in destinations:

                if destination in active_destinations:
                    continue

                operation = (
                    self.build_delete_operation(
                        key=key,
                        destination=destination
                    )
                )

                self.execute_delete(
                    operation
                )

            self.cache.remove(
                key
            )

        self.cache.save()
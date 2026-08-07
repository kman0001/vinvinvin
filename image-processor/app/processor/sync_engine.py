from datetime import datetime, timezone
from pathlib import Path

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

    def __init__(
        self,
        storages
    ):
        self.cache = CacheManager()
        self.storages = storages


    def get_cached_item(
        self,
        key
    ):
        return self.cache.get(
            key
        )


    def find_by_source(
        self,
        source,
        category
    ):
        """
        동일 source + category cache 검색.

        메뉴명이 변경되어
        menu_hash가 변경된 경우
        기존 이미지를 재사용하기 위한 용도.
        """

        for key in self.cache.keys():

            item = self.cache.get(
                key
            )

            if not item:
                continue

            if item.get(
                "source"
            ) != source:
                continue

            if item.get(
                "category"
            ) != category:
                continue

            if item.get(
                "status"
            ) != "success":
                continue


            if not item.get(
                "image_hash"
            ):
                continue

            if not item.get(
                "destination"
            ):
                continue


            return key, item


        return None, None



    def find_reusable_image(
        self,
        image_hash
    ):
        """
        동일 image_hash를 가진
        성공 처리 이미지를 찾는다.

        storage 종류와 관계없이
        현재 활성 storage 중
        실제 파일이 존재하는 것을 반환한다.
        """

        for key in self.cache.keys():

            item = self.cache.get(
                key
            )

            if not item:
                continue


            if item.get(
                "status"
            ) != "success":
                continue


            if item.get(
                "image_hash"
            ) != image_hash:
                continue


            storage_status = item.get(
                "storage",
                {}
            )


            for storage_name, status in storage_status.items():

                if status.get(
                    "status"
                ) != "success":
                    continue


                destination = status.get(
                    "destination"
                )

                if not destination:
                    continue


                storage = None


                for name, obj in self.storages:

                    if name == storage_name:
                        storage = obj
                        break


                if storage is None:
                    continue


                if not storage.exists(
                    destination
                ):
                    continue


                print(
                    "[INFO] Reusable image found: "
                    f"{storage_name}/{destination}",
                    flush=True
                )


                return {
                    "storage_name": storage_name,
                    "storage": storage,
                    "destination": destination,
                    "source_item": item
                }


        return None



    def export_reusable_image(
        self,
        reusable,
        temp_dir
    ):
        """
        기존 storage 이미지 다운로드.

        process_image() 결과와 동일하게
        upload 단계에서 사용할 수 있도록
        임시 output 생성.
        """

        storage = reusable[
            "storage"
        ]

        destination = reusable[
            "destination"
        ]


        output = (
            Path(temp_dir) /
            destination
        )


        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        storage.download(
            destination,
            output
        )


        print(
            "[INFO] Exported reusable image: "
            f"{destination}",
            flush=True
        )


        return output

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
        source_type,
        cached_item
    ):
        """
        기존 cache 유지용.

        현재 runner.py에서는
        직접 사용하지 않지만
        호환성을 위해 유지.
        """

        item = dict(
            cached_item
        )

        item.update({
            "category": category,
            "name": name,
            "source": source,
            "source_type": source_type,
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
        source_type,
        image_hash,
        filename,
        source_key
    ):
        """
        menu_hash 변경 시
        기존 처리 결과를 재사용한다.

        실제 storage 상태는
        현재 활성화된 storage 기준으로 다시 확인한다.
        """

        source_item = (
            self.cache.get(
                source_key
            )
            or {}
        )


        source_storages = source_item.get(
            "storage",
            {}
        )


        storage_status = {}


        for storage_name, storage in self.storages:

            previous = (
                source_storages.get(
                    storage_name,
                    {}
                )
            )


            if (
                previous.get(
                    "status"
                ) == "success"
                and previous.get(
                    "destination"
                ) == filename
                and storage.exists(
                    filename
                )
            ):

                storage_status[storage_name] = {
                    "status": "success",
                    "destination": filename,
                    "image_hash": image_hash,
                    "updated_at": now()
                }

                continue



            if storage.exists(
                filename
            ):

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
                    "Reusable image not found in "
                    f"storage '{storage_name}'."
                ),
                "updated_at": now()
            }


        return self._set_synced_item(
            key=key,
            category=category,
            name=name,
            source=source,
            source_type=source_type,
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
        source_type,
        image_hash,
        filename,
        storage_status
    ):
        """
        cache 저장.

        storage별 상태를 기준으로
        전체 성공 여부를 결정한다.
        """

        failed = [
            storage_name
            for storage_name, status
            in storage_status.items()
            if status.get(
                "status"
            ) == "error"
        ]


        item = {
            "category": category,
            "name": name,
            "source": source,
            "source_type": source_type,
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



    def execute_upload(
        self,
        operation,
        previous_item,
        image_hash
    ):
        """
        활성 storage별 업로드 처리.

        같은 storage:
            동일 hash + 동일 파일 존재
                -> skip

        다른 storage:
            cache 없으면 upload
        """

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
                previous.get(
                    "status"
                ) == "success"
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
                        "[INFO] Removed old image: "
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
        source_type,
        image_hash,
        filename,
        output
    ):

        previous_item = (
            self.cache.get(
                key
            )
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
            source_type=source_type,
            image_hash=image_hash,
            filename=filename,
            storage_status=storage_status
        )



    def build_delete_operation(
        self,
        key,
        destination
    ):
        return DeleteOperation(
            key=key,
            destination=destination
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
                    "[ERROR] Failed deleting stale image "
                    f"{storage_name}/{operation.destination}: {exc}",
                    flush=True
                )



    def remove_stale_items(
        self,
        current_keys
    ):
        """
        현재 메뉴에 존재하지 않는 cache 제거.

        단,
        동일 destination을 사용하는
        다른 메뉴가 있으면 실제 파일은 유지한다.
        """

        stale_keys = (
            self.cache.keys()
            - current_keys
        )


        active_destinations = set()


        for key in current_keys:

            item = self.cache.get(
                key
            )

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
                self.cache.get(
                    key
                )
                or {}
            )


            destinations = set()


            destination = item.get(
                "destination"
            )

            if destination:
                destinations.add(
                    destination
                )


            for status in item.get(
                "storage",
                {}
            ).values():

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


                operation = self.build_delete_operation(
                    key=key,
                    destination=destination
                )


                self.execute_delete(
                    operation
                )


            self.cache.remove(
                key
            )


        self.cache.save()        
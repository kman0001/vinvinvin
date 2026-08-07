import shutil
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from app.processor.hash import calculate_hash, calculate_menu_hash
from app.processor.image import process_image
from app.processor.sync_engine import SyncEngine
from app.source import SourceError, load_menu
from app.storage import create_storage


CATEGORY_MAP = {
    "글라스 와인": "Glass",
    "레드": "Red",
    "화이트": "White",
    "스파클링": "Sparkling",
    "맥주": "Beer",
    "위스키": "Whiskey",
    "꼬냑": "Cognac",
    "안주": "Snack",
}


LOCAL_IMAGE_DIR = Path("/app/images")


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


def find_local_image(filename):
    """
    Find an original image in the shared /app/images directory.

    The Google Sheet may contain:
        foo.png
        foo.jpg
        foo.jpeg
        foo.webp

    Only the exact filename is preferred.
    """

    if not filename:
        return None

    filename = Path(filename).name

    source = LOCAL_IMAGE_DIR / filename

    if source.is_file():
        return source

    return None


def is_ignored_image(filename):
    """
    Images beginning with no-image are placeholders and must not
    be processed or uploaded.
    """

    if not filename:
        return False

    return Path(filename).name.lower().startswith(
        "no-image"
    )


def process_local_source(
    source,
    temp_dir
):
    """
    Copy a local source image into the temporary working directory.

    This prevents the original image in /app/images from being modified.
    """

    local_source = temp_dir / "source"

    shutil.copy2(
        source,
        local_source
    )

    return local_source


def process_images(config):
    print(
        "Image processing started",
        flush=True
    )

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

    sync_engine = SyncEngine(
        storages
    )

    current_keys = set()

    for index, item in enumerate(menu):

        if not item.category or not item.name or not item.photo:

            print(
                f"[WARN] menu[{index}] lacks 종류, 이름, or 사진; skipped.",
                flush=True
            )

            continue

        if is_ignored_image(item.photo):

            print(
                f"[INFO] Ignored placeholder image: {item.photo}",
                flush=True
            )

            continue

        menu_hash = calculate_menu_hash(
            item.category,
            item.name
        )

        current_keys.add(
            menu_hash
        )

        cached_item = sync_engine.get_cached_item(
            menu_hash
        )

        expected_prefix = (
            f"{get_category_prefix(item.category)}_"
        )

        cached_destination = (
            cached_item.get("destination", "")
            if cached_item
            else ""
        )

        same_destination = (
            cached_destination.startswith(
                expected_prefix
            )
        )

        # ----------------------------------------------------------
        # 1. 동일 메뉴 + 동일 source
        #
        # 기존 처리 결과를 재사용할 수 있는지 판단한다.
        #
        # 실제 storage 재사용 여부는 image_hash 계산 후 결정된다.
        # ----------------------------------------------------------

        has_cached_item = (
            cached_item
            and cached_item.get("source") == item.photo
            and cached_item.get("image_hash")
            and cached_destination
            and same_destination
        )

        # ----------------------------------------------------------
        # 2. 같은 category + 같은 source
        #
        # 메뉴명이 변경되어 menu_hash가 달라졌더라도
        # 기존 이미지를 재사용한다.
        # ----------------------------------------------------------

        source_key, source_item = (
            sync_engine.find_by_source(
                item.photo,
                item.category
            )
        )

        if (
            source_item
            and source_key != menu_hash
            and source_item.get("image_hash")
            and source_item.get("destination")
        ):

            sync_engine.reuse_item(
                key=menu_hash,
                category=item.category,
                name=item.name,
                source=item.photo,
                source_type=(
                    "url"
                    if item.is_url
                    else "local"
                ),
                image_hash=source_item["image_hash"],
                filename=source_item["destination"],
                source_key=source_key
            )

            print(
                f"[INFO] Reused cached image: {item.name}",
                flush=True
            )

            continue

        # ----------------------------------------------------------
        # 3. 실제 source 준비
        #
        # URL:
        #     다운로드
        #
        # 로컬 파일:
        #     /app/images에서 원본 탐색 후 임시 폴더로 복사
        # ----------------------------------------------------------

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

                if item.is_url:

                    print(
                        f"[INFO] Downloading: {item.name}",
                        flush=True
                    )

                    download(
                        item.photo,
                        source,
                        timeout
                    )

                else:

                    local_source = find_local_image(
                        item.photo
                    )

                    if local_source is None:

                        print(
                            "[ERROR] Local image not found: "
                            f"{item.photo}",
                            flush=True
                        )

                        continue

                    print(
                        f"[INFO] Using local image: "
                        f"{item.name} <- {local_source.name}",
                        flush=True
                    )

                    process_local_source(
                        local_source,
                        temp_dir
                    )

                # --------------------------------------------------
                # 4. 원본 hash
                # --------------------------------------------------

                image_hash = calculate_hash(
                    source
                )

                filename = (
                    f"{get_category_prefix(item.category)}_"
                    f"{image_hash[:16]}.webp"
                )

                # --------------------------------------------------
                # 5. 기존 처리 이미지 재사용 확인
                # --------------------------------------------------

                reusable = (
                    sync_engine.find_reusable_image(
                        image_hash
                    )
                )

                # --------------------------------------------------
                # 6. 이미지 처리 또는 기존 결과 재사용
                # --------------------------------------------------

                if reusable:

                    print(
                        "[INFO] Reusing processed image: "
                        f"{filename}",
                        flush=True
                    )

                    output = (
                        sync_engine.export_reusable_image(
                            reusable,
                            temp_dir
                        )
                    )

                else:

                    output = process_image(
                        source,
                        item.category,
                        temp_dir,
                        filename
                    )

                # --------------------------------------------------
                # 7. storage 동기화
                # --------------------------------------------------

                result = sync_engine.sync_item(
                    key=menu_hash,
                    category=item.category,
                    name=item.name,
                    source=item.photo,
                    source_type=(
                        "url"
                        if item.is_url
                        else "local"
                    ),
                    image_hash=image_hash,
                    filename=filename,
                    output=output
                )

                if result.get("status") == "success":

                    print(
                        f"[INFO] Processed: "
                        f"{item.name} -> {filename}",
                        flush=True
                    )

                else:

                    print(
                        f"[ERROR] Processing failed: "
                        f"{item.name} -> "
                        f"{result.get('error')}",
                        flush=True
                    )

        except Exception as exc:

            print(
                f"[ERROR] Failed to process "
                f"{item.name}: {exc}",
                flush=True
            )

    # --------------------------------------------------------------
    # 8. 현재 메뉴에 없는 cache 및 storage 파일 정리
    # --------------------------------------------------------------

    sync_engine.remove_stale_items(
        current_keys
    )

    print(
        "Image processing finished",
        flush=True
    )
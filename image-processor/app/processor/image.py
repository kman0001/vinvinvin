import io
from pathlib import Path

from PIL import Image
from rembg import remove


TARGET_OBJECT_HEIGHT = 800


def has_transparency(image: Image.Image) -> bool:
    """
    이미지에 실제 투명 영역이 있는지 검사한다.

    P 모드의 palette transparency도 실제 alpha 채널로 변환해서 검사한다.
    """

    print(
        "[IMAGE CHECK] "
        f"mode={image.mode}",
        flush=True
    )

    # Palette 이미지
    if image.mode == "P":
        transparency = image.info.get("transparency")

        if transparency is not None:
            print(
                "[IMAGE CHECK] "
                "palette transparency detected",
                flush=True
            )

            converted = image.convert("RGBA")

            alpha = converted.getchannel("A")
            alpha_min, alpha_max = alpha.getextrema()

            print(
                "[IMAGE CHECK] "
                f"alpha_min={alpha_min}, "
                f"alpha_max={alpha_max}",
                flush=True
            )

            return alpha_min < 255

        print(
            "[IMAGE CHECK] "
            "palette image without transparency -> opaque",
            flush=True
        )

        return False

    # Alpha 채널이 없는 이미지
    if "A" not in image.getbands():
        print(
            "[IMAGE CHECK] "
            "no alpha channel -> opaque",
            flush=True
        )

        return False

    alpha = image.getchannel("A")

    alpha_min, alpha_max = alpha.getextrema()

    print(
        "[IMAGE CHECK] "
        f"alpha_min={alpha_min}, "
        f"alpha_max={alpha_max}",
        flush=True
    )

    return alpha_min < 255


def ensure_rgba_if_transparent(
    image: Image.Image
) -> Image.Image:
    """
    투명도가 있는 이미지가 P 모드 등으로 남아있으면
    RGBA로 변환하여 palette transparency를 보존한다.

    특히 P -> RGB 변환으로 투명 배경이 색상으로 굳는 문제를 방지한다.
    """

    if image.mode == "P":
        transparency = image.info.get("transparency")

        if transparency is not None:
            print(
                "[IMAGE PROCESS] "
                "converting palette image P -> RGBA "
                "while preserving transparency",
                flush=True
            )

            image = image.convert("RGBA")

            alpha = image.getchannel("A")
            alpha_min, alpha_max = alpha.getextrema()

            print(
                "[IMAGE PROCESS] "
                f"alpha preserved: "
                f"min={alpha_min}, "
                f"max={alpha_max}",
                flush=True
            )

            return image

        print(
            "[IMAGE PROCESS] "
            "palette image P without transparency -> RGB",
            flush=True
        )

        return image.convert("RGB")

    return image


def resize_to_800(
    image: Image.Image
) -> Image.Image:
    """
    전체 캔버스가 아니라 실제 객체 영역을 기준으로
    높이가 최대 800px이 되도록 조정한다.

    투명 영역을 제외한 alpha bounding box를 기준으로 한다.
    """

    # 투명도를 사용할 수 있도록 RGBA로 변환
    if image.mode not in {"RGB", "RGBA"}:
        image = ensure_rgba_if_transparent(
            image
        )

    if "A" not in image.getbands():
        print(
            "[IMAGE SIZE] "
            "no alpha channel -> "
            "canvas size used",
            flush=True
        )

        return image

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if not bbox:
        print(
            "[IMAGE SIZE] "
            "no visible object detected",
            flush=True
        )

        return image

    left, top, right, bottom = bbox

    object_width = right - left
    object_height = bottom - top

    print(
        "[IMAGE SIZE] "
        f"canvas={image.width}x{image.height}, "
        f"object={object_width}x{object_height}",
        flush=True
    )

    if object_height <= TARGET_OBJECT_HEIGHT:
        print(
            "[IMAGE SIZE] "
            f"object height <= {TARGET_OBJECT_HEIGHT} "
            "-> resize skipped",
            flush=True
        )

        return image

    scale = (
        TARGET_OBJECT_HEIGHT /
        object_height
    )

    new_size = (
        round(image.width * scale),
        round(image.height * scale)
    )

    print(
        "[IMAGE SIZE] "
        f"resize -> "
        f"{new_size[0]}x{new_size[1]}",
        flush=True
    )

    return image.resize(
        new_size,
        Image.Resampling.LANCZOS
    )


def process_image(
    source: Path,
    category: str,
    output_dir: Path,
    filename: str
) -> Path:
    """
    Process an image and save it as WebP.
    """

    with Image.open(source) as opened:
        print(
            "[IMAGE CHECK] "
            f"source={source.name}, "
            f"format={opened.format}, "
            f"mode={opened.mode}, "
            f"size={opened.size}",
            flush=True
        )

        opened.load()

        # palette transparency 정보가 copy 과정에서도 유지되도록
        # 원본의 info를 보존한다.
        image = opened.copy()

        if opened.info.get("transparency") is not None:
            image.info["transparency"] = (
                opened.info["transparency"]
            )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    transparent = has_transparency(
        image
    )

    print(
        "[IMAGE CHECK] "
        f"has_transparency={transparent}",
        flush=True
    )

    # ---------------------------------------------------------
    # Palette transparency -> RGBA
    # ---------------------------------------------------------
    #
    # 중요:
    # P + transparency 이미지를 RGB로 바꾸면
    # 투명 영역이 palette 색상으로 굳을 수 있다.
    #
    # 따라서 background removal 여부를 결정한 직후
    # 투명 이미지라면 반드시 RGBA로 변환한다.
    #
    if transparent:
        image = ensure_rgba_if_transparent(
            image
        )

    # ---------------------------------------------------------
    # Background removal
    # ---------------------------------------------------------

    if category == "안주":
        print(
            "[IMAGE PROCESS] "
            "category=안주 "
            "-> background removal skipped",
            flush=True
        )

    elif transparent:
        print(
            "[IMAGE PROCESS] "
            "existing transparency detected "
            "-> background removal skipped",
            flush=True
        )

    else:
        print(
            "[IMAGE PROCESS] "
            "no transparency detected "
            "-> background removal applied",
            flush=True
        )

        result = remove(
            image
        )

        if isinstance(result, Image.Image):
            image = result

        else:
            with Image.open(
                io.BytesIO(result)
            ) as removed:
                removed.load()

                image = removed.convert(
                    "RGBA"
                )

        print(
            "[IMAGE PROCESS] "
            f"rembg result mode={image.mode}, "
            f"size={image.size}",
            flush=True
        )

    # ---------------------------------------------------------
    # 실제 객체 영역 기준 800px
    # ---------------------------------------------------------

    image = resize_to_800(
        image
    )

    # ---------------------------------------------------------
    # 저장 전 최종 모드 정리
    # ---------------------------------------------------------

    if image.mode == "P":
        transparency = image.info.get(
            "transparency"
        )

        if transparency is not None:
            print(
                "[IMAGE PROCESS] "
                "final P -> RGBA "
                "with transparency preserved",
                flush=True
            )

            image = image.convert(
                "RGBA"
            )

        else:
            print(
                "[IMAGE PROCESS] "
                "final P -> RGB",
                flush=True
            )

            image = image.convert(
                "RGB"
            )

    elif image.mode not in {
        "RGB",
        "RGBA"
    }:
        print(
            "[IMAGE PROCESS] "
            f"converting unsupported mode "
            f"{image.mode}",
            flush=True
        )

        image = image.convert(
            "RGBA"
            if "A" in image.getbands()
            else "RGB"
        )

    # ---------------------------------------------------------
    # 최종 alpha 상태 확인
    # ---------------------------------------------------------

    if image.mode == "RGBA":
        alpha = image.getchannel("A")

        alpha_min, alpha_max = (
            alpha.getextrema()
        )

        print(
            "[IMAGE PROCESS] "
            f"final alpha: "
            f"min={alpha_min}, "
            f"max={alpha_max}",
            flush=True
        )

    destination = (
        output_dir /
        filename
    )

    image.save(
        destination,
        format="WEBP",
        quality=90,
        method=6
    )

    print(
        "[IMAGE PROCESS] "
        f"saved={destination.name}, "
        f"mode={image.mode}, "
        f"size={image.size}",
        flush=True
    )

    return destination
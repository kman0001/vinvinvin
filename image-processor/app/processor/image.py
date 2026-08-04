import io
from pathlib import Path

from PIL import Image
from rembg import remove


def has_transparency(image: Image.Image) -> bool:
    if image.mode == "P" and "transparency" in image.info:
        return True

    if "A" not in image.getbands():
        return False

    return image.getchannel("A").getextrema()[0] < 255


def resize_to_800(image: Image.Image) -> Image.Image:
    if image.height <= 800:
        return image

    return image.resize(
        (
            round(image.width * 800 / image.height),
            800
        ),
        Image.Resampling.LANCZOS
    )


def process_image(
    source: Path,
    category: str,
    output_dir: Path,
    filename: str
) -> Path:
    """Process an image and save it as WebP."""

    with Image.open(source) as opened:
        opened.load()
        image = opened.copy()

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # 안주는 배경 제거 없이 리사이즈만 한다.
    if category != "안주" and not has_transparency(image):
        result = remove(image)
        image = (
            result
            if isinstance(result, Image.Image)
            else Image.open(io.BytesIO(result))
        )

    image = resize_to_800(image)

    destination = output_dir / filename

    # WebP 저장 시 지원되지 않는 일부 모드는 RGB/RGBA로 변환
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert(
            "RGBA" if "A" in image.getbands() else "RGB"
        )

    image.save(
        destination,
        format="WEBP",
        quality=90,
        method=6
    )

    return destination
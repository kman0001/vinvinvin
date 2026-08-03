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
    return image.resize((round(image.width * 800 / image.height), 800), Image.Resampling.LANCZOS)


def source_extension(image: Image.Image) -> str:
    return {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif"}.get(
        image.format or "", ".png"
    )


def process_image(source: Path, category: str, output_dir: Path, stem: str) -> Path:
    """Process a URL image. Snacks retain their source format and only resize."""
    with Image.open(source) as opened:
        opened.load()
        image = opened.copy()
        original_format = opened.format or "PNG"
        extension = source_extension(opened)

    output_dir.mkdir(parents=True, exist_ok=True)
    if category == "안주":
        image = resize_to_800(image)
        destination = output_dir / f"{stem}{extension}"
        if original_format == "JPEG" and image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        image.save(destination, format=original_format)
        return destination

    if not has_transparency(image):
        result = remove(image)
        image = result if isinstance(result, Image.Image) else Image.open(io.BytesIO(result))
    image = resize_to_800(image)
    destination = output_dir / f"{stem}.webp"
    image.save(destination, format="WEBP", quality=90, method=6)
    return destination

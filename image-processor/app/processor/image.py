import io
import os
from pathlib import Path

from PIL import Image
from rembg import remove, new_session


TARGET_HEIGHT = 800

REMBG_SESSION = None


def get_rembg_session():
    """
    rembg 모델 lazy loading.

    최초 배경 제거 시 모델 로딩.
    이후 같은 컨테이너에서는 메모리 재사용.
    """

    global REMBG_SESSION

    if REMBG_SESSION is None:

        model_home = os.getenv(
            "U2NET_HOME",
            "/tmp/u2net"
        )

        os.environ["U2NET_HOME"] = model_home

        print(
            "[IMAGE PROCESS] "
            "loading rembg model",
            flush=True
        )

        REMBG_SESSION = new_session(
            "u2net"
        )

        print(
            "[IMAGE PROCESS] "
            "rembg model ready",
            flush=True
        )

    return REMBG_SESSION


def has_transparency(
    image: Image.Image
) -> bool:
    """
    실제 투명 영역 확인
    """

    if "A" not in image.getbands():
        return False

    alpha = image.getchannel("A")

    alpha_min, _ = alpha.getextrema()

    return alpha_min < 255


def resize_to_800(
    image: Image.Image
) -> Image.Image:
    """
    투명 객체 기준 최대 높이 800px.

    누끼 이미지:
    - alpha bbox 기준

    일반 이미지:
    - resize 하지 않음
    """

    if "A" not in image.getbands():
        return image

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if not bbox:
        return image

    _, top, _, bottom = bbox

    object_height = bottom - top

    if object_height <= TARGET_HEIGHT:
        return image

    scale = (
        TARGET_HEIGHT /
        object_height
    )

    new_size = (
        round(image.width * scale),
        round(image.height * scale)
    )

    return image.resize(
        new_size,
        Image.Resampling.LANCZOS
    )


def convert_result_to_image(
    result
) -> Image.Image:
    """
    rembg 결과 타입 정리.
    """

    if isinstance(
        result,
        Image.Image
    ):
        return result

    with Image.open(
        io.BytesIO(result)
    ) as image:

        image.load()

        return image.convert(
            "RGBA"
        )


def process_image(
    source: Path,
    category: str,
    output_dir: Path,
    filename: str
) -> Path:
    """
    이미지 처리:

    - 안주:
        배경 제거 X

    - 투명 이미지:
        배경 제거 X

    - 일반 이미지:
        rembg 처리

    - 객체 높이 기준 800px resize

    - WebP 저장
    """

    with Image.open(source) as opened:

        opened.load()

        image = opened.convert(
            "RGBA"
        )


    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    transparent = has_transparency(
        image
    )


    #
    # Background removal
    #

    if (
        category != "안주"
        and not transparent
    ):

        result = remove(
            image,
            session=get_rembg_session()
        )

        image = convert_result_to_image(
            result
        )


    #
    # Resize
    #

    image = resize_to_800(
        image
    )


    #
    # WebP 저장
    #

    destination = (
        output_dir /
        filename
    )


    if image.mode not in {
        "RGB",
        "RGBA"
    }:

        image = image.convert(
            "RGBA"
        )


    image.save(
        destination,
        format="WEBP",
        quality=90,
        method=6
    )


    return destination
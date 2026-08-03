import re
import unicodedata


TYPE_MAP = {

    "레드": "Red",

    "화이트": "White",

    "로제": "Rose",

    "스파클링": "Sparkling",

    "샴페인": "Champagne",

    "안주": "Snack"

}


def canonical_name(
    wine_type: str,
    name: str
):

    wine_type = TYPE_MAP.get(
        wine_type,
        wine_type
    )

    text = f"{wine_type}_{name}"

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = text.encode(
        "ascii",
        "ignore"
    ).decode()

    text = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        text
    )

    text = re.sub(
        "_+",
        "_",
        text
    )

    return text.strip("_")
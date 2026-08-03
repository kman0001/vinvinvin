import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_CONSTANTS_FILE = Path("/app/website/js/config/constants.js")
DEFAULT_CONSTANTS_PATH = "/js/config/constants.js"
API_EXPORT_RE = re.compile(
    r"export\s+const\s+API\s*=\s*([\"'])(?P<url>https?://.+?)\1\s*;",
    re.DOTALL
)


class SourceError(RuntimeError):
    """Raised when the Apps Script response cannot be used as a menu source."""


@dataclass(frozen=True, slots=True)
class MenuImage:
    category: str
    name: str
    photo: str

    @property
    def is_url(self) -> bool:
        return urlparse(self.photo).scheme in {"http", "https"}


    @property
    def is_local_webp(self) -> bool:
        return not self.is_url and self.photo.split("?", 1)[0].lower().endswith(".webp")


def parse_apps_script_url(constants_source: str, label: str = "constants.js") -> str:
    match = API_EXPORT_RE.search(constants_source)
    if not match:
        raise SourceError(f"Could not find export const API in {label}.")

    return match.group("url").strip()


def read_apps_script_url(constants_file: Path) -> str:
    try:
        source = constants_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"Could not read website constants file: {constants_file}") from exc

    return parse_apps_script_url(source, str(constants_file))


def fetch_apps_script_url(constants_url: str, timeout: int) -> str:
    request = Request(
        constants_url,
        headers={
            "Accept": "application/javascript,text/javascript,text/plain,*/*",
            "User-Agent": "vinvinvin-image-processor/1.0"
        }
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - operator config
            source = response.read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceError(f"Could not load website constants URL: {constants_url}") from exc

    return parse_apps_script_url(source, constants_url)


def build_constants_url(base_url: str, constants_path: str = DEFAULT_CONSTANTS_PATH) -> str:
    base_url = base_url.strip()
    constants_path = constants_path.strip() or DEFAULT_CONSTANTS_PATH
    if not base_url:
        return ""
    if urlparse(base_url).scheme not in {"http", "https"}:
        raise SourceError("source.base_url must start with http:// or https://.")
    return urljoin(base_url.rstrip("/") + "/", constants_path.lstrip("/"))


def get_constants_url(config: dict) -> str:
    source_config = config.get("source", {})
    base_url = (
        os.environ.get("WEBSITE_BASE_URL", "").strip()
        or source_config.get("base_url", "").strip()
    )
    if base_url:
        return build_constants_url(
            base_url,
            source_config.get("constants_path", DEFAULT_CONSTANTS_PATH)
        )

    return (
        os.environ.get("WEBSITE_CONSTANTS_URL", "").strip()
        or source_config.get("constants_url", "").strip()
        or source_config.get("url", "").strip()
    )


def get_source_url(config: dict) -> str:
    timeout = config.get("source", {}).get("timeout_seconds", 30)
    constants_url = get_constants_url(config)

    if constants_url:
        return fetch_apps_script_url(constants_url, timeout)

    constants_file = Path(
        os.environ.get("WEBSITE_CONSTANTS_FILE", str(DEFAULT_CONSTANTS_FILE))
    )
    return read_apps_script_url(constants_file)


def parse_menu(payload: object) -> list[MenuImage]:
    if not isinstance(payload, dict) or not isinstance(payload.get("menu"), list):
        raise SourceError("Apps Script JSON must contain a menu array.")

    items = []
    for index, row in enumerate(payload["menu"]):
        if not isinstance(row, dict):
            continue
        category = str(row.get("종류", "")).strip()
        name = str(row.get("이름", "")).strip()
        photo = str(row.get("사진", "")).strip()
        if not (category and name and photo):
            print(f"[WARN] menu[{index}] lacks 종류, 이름, or 사진; skipped.", flush=True)
            continue
        items.append(MenuImage(category=category, name=name, photo=photo))

    return items


def load_menu(config: dict) -> list[MenuImage]:
    url = get_source_url(config)
    if not url:
        raise SourceError("Set source.base_url to the website root URL.")

    timeout = config.get("source", {}).get("timeout_seconds", 30)
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - website operator config
            payload = json.load(response)
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceError(f"Could not load Apps Script JSON: {exc}") from exc

    return parse_menu(payload)

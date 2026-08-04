import json
from pathlib import Path


CACHE_FILE = Path(
    "/app/config/cache.json"
)

DEFAULT_CACHE = {
    "version": 1,
    "items": {}
}


class CacheManager:

    def __init__(self):
        self.data = {
            "version": DEFAULT_CACHE["version"],
            "items": {}
        }

        self.load()


    def load(self):
        if not CACHE_FILE.exists():
            return

        try:
            loaded = json.loads(
                CACHE_FILE.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError
        ):
            return

        if not isinstance(
            loaded,
            dict
        ):
            return

        items = loaded.get(
            "items"
        )

        if not isinstance(
            items,
            dict
        ):
            return

        self.data = {
            "version": loaded.get(
                "version",
                DEFAULT_CACHE["version"]
            ),
            "items": items
        }


    def save(self):
        CACHE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        CACHE_FILE.write_text(
            json.dumps(
                self.data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )


    def get(
        self,
        key
    ):
        return self.data[
            "items"
        ].get(key)


    def set(
        self,
        key,
        value
    ):
        self.data[
            "items"
        ][key] = value


    def remove(
        self,
        key
    ):
        self.data[
            "items"
        ].pop(
            key,
            None
        )


    def keys(self):
        return set(
            self.data[
                "items"
            ].keys()
        )
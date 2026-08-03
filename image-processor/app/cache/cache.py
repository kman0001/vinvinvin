import json
from pathlib import Path


DEFAULT_CACHE = {
    "version": 1,
    "items": {}
}


class CacheManager:

    def __init__(self):

        self.path = Path(
            "/app/config/cache.json"
        )

        self.data = DEFAULT_CACHE.copy()

        self.load()


    def load(self):

        if not self.path.exists():
            return

        try:
            loaded = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                ) or "{}"
            )
        except json.JSONDecodeError:
            return

        if isinstance(loaded, dict) and isinstance(loaded.get("items"), dict):
            self.data = {
                "version": loaded.get("version", DEFAULT_CACHE["version"]),
                "items": loaded["items"]
            }


    def save(self):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.path.write_text(

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

        return self.data["items"].get(key)


    def set(
        self,
        key,
        value
    ):

        self.data["items"][key] = value


    def remove(
        self,
        key
    ):

        self.data["items"].pop(
            key,
            None
        )


    def keys(self):

        return set(
            self.data["items"].keys()
        )

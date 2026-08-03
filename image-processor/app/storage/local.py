from pathlib import Path
import shutil

from app.storage.base import Storage


class LocalStorage(Storage):

    def __init__(self, config):
        super().__init__(config)

        self.base_path = Path(
            config["path"]
        )

        self.base_path.mkdir(
            parents=True,
            exist_ok=True
        )


    def upload(
        self,
        source: Path,
        destination: str
    ):
        target = self.base_path / destination

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            source,
            target
        )


    def delete(
        self,
        destination: str
    ):
        target = self.base_path / destination

        if target.exists():
            target.unlink()


    def exists(
        self,
        destination: str
    ):
        return (
            self.base_path / destination
        ).exists()
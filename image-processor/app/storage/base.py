from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):

    def __init__(self, config):
        self.config = config


    @abstractmethod
    def upload(
        self,
        source: Path,
        destination: str
    ):
        pass


    @abstractmethod
    def delete(
        self,
        destination: str
    ):
        pass


    @abstractmethod
    def exists(
        self,
        destination: str
    ) -> bool:
        pass
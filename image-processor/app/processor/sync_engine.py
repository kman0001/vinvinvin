from app.cache.cache import CacheManager


class SyncEngine:

    def __init__(

        self,

        storages

    ):

        self.cache = CacheManager()

        self.storages = storages


    def sync(

        self,

        images

    ):

        pass
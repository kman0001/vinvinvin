from app.storage.local import LocalStorage


def create_storage(name, config):

    storage_type = config.get(
        "type"
    )

    if storage_type == "local":
        return LocalStorage(config)


    raise ValueError(
        f"Unsupported storage type: {storage_type}"
    )
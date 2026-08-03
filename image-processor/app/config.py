import json
from pathlib import Path


CONFIG_DIR = Path("/app/config")
CONFIG_FILE = CONFIG_DIR / "config.json"


DEFAULT_CONFIG = {
    "source": {"base_url": "", "constants_path": "/js/config/constants.js", "timeout_seconds": 30},

    "scheduler": {
        "enabled": False,
        "cron": "0 3,15 * * *"
    },

    "storage": {
        "github": {
            "enabled": False,
            "type": "github",
            "repository": "",
            "branch": "main",
            "path": "website/images",
            "token_env": "GITHUB_TOKEN",
            "token": ""
        },

        "local": {
            "enabled": False,
            "type": "local",
            "path": "/app/images"
        },

        "r2": {
            "enabled": False,
            "type": "s3",
            "endpoint": "",
            "bucket": "",
            "path": "",
            "access_key_env": "R2_ACCESS_KEY",
            "secret_key_env": "R2_SECRET_KEY",
            "access_key": "",
            "secret_key": ""
        },

        "s3": {
            "enabled": False,
            "type": "s3",
            "region": "",
            "bucket": "",
            "path": "",
            "access_key_env": "AWS_ACCESS_KEY_ID",
            "secret_key_env": "AWS_SECRET_ACCESS_KEY",
            "access_key": "",
            "secret_key": ""
        }
    }
}


def create_default_config():
    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with CONFIG_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            DEFAULT_CONFIG,
            f,
            indent=2,
            ensure_ascii=False
        )


def load_config():
    if not CONFIG_FILE.exists():
        create_default_config()

        print(
            "[WARN] config.json not found.",
            flush=True
        )

        print(
            f"[INFO] Created default config: {CONFIG_FILE}",
            flush=True
        )

        print(
            "[WARN] Please edit config.json and restart container.",
            flush=True
        )

        return None


    try:
        with CONFIG_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        print(
            f"[ERROR] Invalid config.json: {e}",
            flush=True
        )

        return None
import logging
from pathlib import Path

from eldial.core.config import get_config


def setup_logging(level: int = logging.INFO) -> None:
    config = get_config()
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.logs_dir / "eldial.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

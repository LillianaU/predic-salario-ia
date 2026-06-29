import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerObserver:
    _handlers: list = []

    @classmethod
    def attach(cls, handler: logging.Handler) -> None:
        cls._handlers.append(handler)


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    LoggerObserver.attach(ch)
    if log_file:
        fh = RotatingFileHandler(
            str(log_file),
            maxBytes=1_048_576,
            backupCount=5,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        LoggerObserver.attach(fh)
    return logger

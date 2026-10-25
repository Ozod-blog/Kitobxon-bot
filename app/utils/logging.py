import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
def setup_logging(level: str = "INFO"):
    Path("logs").mkdir(exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    stream = logging.StreamHandler(); stream.setFormatter(fmt); root.addHandler(stream)
    file = RotatingFileHandler("logs/kitobxon.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file.setFormatter(fmt); root.addHandler(file)

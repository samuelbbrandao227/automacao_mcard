import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%d/%m/%Y %H:%M:%S"
)

logger = logging.getLogger(__name__)
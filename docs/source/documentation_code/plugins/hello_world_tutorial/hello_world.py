import structlog
from dioptra import pyplugs

logger = structlog.get_logger(__name__)

@pyplugs.register
def hello_world():
    logger.info("Hello, World! Welcome to Dioptra.")
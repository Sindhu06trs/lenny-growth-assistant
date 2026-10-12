import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configures structured logging for the application.
    Ensures safe formatting without logging secrets or credentials.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("lenny_growth_api")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()

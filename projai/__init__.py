import logging
from logging import NullHandler
from logging.config import dictConfig
from importlib.metadata import version

from .apps import AppProjectInovafit
from .settings import CONFIG_LOG

# __version__ = version("projai")
dictConfig(CONFIG_LOG)
# Set default logging handler to avoid
# 'No handler found' warnings.
logging.getLogger(__name__).addHandler(NullHandler())

__all__ = [
    'AppProjectInovafit'
]

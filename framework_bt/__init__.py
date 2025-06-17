"""
Framework-BT  –  API pública
Solo re-exportamos la función extract para que pueda usarse así:
    from framework_bt import extract
"""
from .extractor import extract

__all__ = ["extract"]
__version__ = "0.0.2"

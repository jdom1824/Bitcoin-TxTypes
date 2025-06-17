"""
Framework-BT – Public API
=========================

This module exposes the main `extract` function as the public interface.

Example usage:
--------------
    from framework_bt import extract, RpcSource, StandardClassifier

    source = RpcSource("http://user:pass@localhost:8332", start_height=0, end_height=0)
    classifier = StandardClassifier()
    for utxo in extract(source, classifier):
        print(utxo)

Currently exported:
-------------------
- extract: UTXO extractor function from multiple data sources.

More components (sources, classifiers) can be imported directly from submodules.
"""

from .extractor import extract

__all__ = ["extract"]
__version__ = "0.0.2"

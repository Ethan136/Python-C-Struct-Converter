# C++ Struct Memory Parser - MVP Architecture
# This package implements a GUI tool for parsing C++ struct memory layouts
# using the Model-View-Presenter (MVP) architectural pattern.

__version__ = "1.0.0"
__author__ = "C++ Struct Parser Team"

try:
    from .presenter import StructPresenter
except Exception:
    StructPresenter = None

from .model import StructModel  # convenience re-export
from .export.csv_export import DefaultCsvExportService, CsvExportOptions, CsvExportError

__all__ = [
    "StructPresenter",
    "StructModel",
    "DefaultCsvExportService",
    "CsvExportOptions",
    "CsvExportError",
]

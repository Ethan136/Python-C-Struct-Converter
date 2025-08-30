# C++ Struct Memory Parser - MVP Architecture
# This package implements a GUI tool for parsing C++ struct memory layouts
# using the Model-View-Presenter (MVP) architectural pattern.

__version__ = "1.0.0"
__author__ = "C++ Struct Parser Team"

try:
    from .presenter import StructPresenter, V7Presenter
except Exception:
    StructPresenter = None
    V7Presenter = None

from .model import StructModel  # convenience re-export
from .export.csv_export import DefaultCsvExportService, CsvExportOptions, CsvExportError

__all__ = [
    "StructPresenter",
    "V7Presenter",
    "StructModel",
    "DefaultCsvExportService",
    "CsvExportOptions",
    "CsvExportError",
]

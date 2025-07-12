import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from model.struct_model import StructModel
from view.struct_view import StructView
from presenter.struct_presenter import StructPresenter
from utils import string_parser

if __name__ == "__main__":
    strings_path = os.path.join(os.path.dirname(__file__), "ui_strings.xml")
    string_parser.load_ui_strings(strings_path)

    model = StructModel()
    presenter = StructPresenter(model, None)  # View will set itself on init
    view = StructView(presenter)
    presenter.view = view
    view.mainloop()
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from model import StructModel
from view import StructView
from presenter import StructPresenter
from config import load_ui_strings

def main():
    """Main application entry point"""
    strings_path = os.path.join(os.path.dirname(__file__), "config", "ui_strings.xml")
    load_ui_strings(strings_path)

    model = StructModel()
    presenter = StructPresenter(model, None)  # View will set itself on init
    view = StructView(presenter)
    presenter.view = view
    view.mainloop()

if __name__ == "__main__":
    main()
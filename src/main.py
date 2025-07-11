import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from model.struct_model import StructModel
from view.struct_view import StructView
from presenter.struct_presenter import StructPresenter

if __name__ == "__main__":
    model = StructModel()
    view = StructView(None) # Presenter will be set after creation
    presenter = StructPresenter(model, view)
    view.presenter = presenter # Set the presenter reference in the view
    view.mainloop()

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from model.struct_model import StructModel
from view.struct_view import StructView
from presenter.struct_presenter import StructPresenter

if __name__ == "__main__":
    model = StructModel()
    presenter = StructPresenter(model, None) # Temporarily set view to None, will be set by view's __init__
    view = StructView(presenter) # Pass the presenter to the view during initialization
    presenter.view = view # Ensure presenter also has a reference to the view
    view.mainloop()
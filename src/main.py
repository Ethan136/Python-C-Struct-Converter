import os
import sys
if getattr(sys, 'frozen', False):
    # 加入 src 目錄和 exe 目錄
    sys.path.append(os.path.join(os.path.dirname(sys.executable), 'src'))
    sys.path.append(os.path.dirname(sys.executable))
else:
    # 加入 src 目錄和專案根目錄
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '')))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model import StructModel
from view import StructView
from presenter import StructPresenter
from config import load_ui_strings


def main():
    """Main application entry point"""
    strings_path = os.path.join(os.path.dirname(__file__), "config", "ui_strings.xml")
    load_ui_strings(strings_path)

    model = StructModel()
    presenter = StructPresenter(model)
    view = StructView(presenter=presenter)
    presenter.view = view  # 確保 presenter 有 view 屬性
    view.mainloop()

if __name__ == "__main__":
    main()
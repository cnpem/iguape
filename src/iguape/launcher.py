# This is part of the source code for the Paineira Graphical User Interface - Iguape
# The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
Execution script. It goes to the directory where Iguape is installed and it executes the program (iguape.py)
"""

from qtpy.QtWidgets import QApplication
from .iguape import Window
import sys


def main():
    """_summary_"""
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

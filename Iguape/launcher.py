#This is part of the source code for the Paineira Graphical User Interface - Iguape
#The code is distributed under the GNU GPL-3.0 License. Please refer to the main page (https://github.com/cnpem/iguape) for more information

"""
Execution script. It goes to the directory where Iguape is installed and it executes the program (iguape.py)
"""

import subprocess
import os


def main():
    """_summary_
    """    
    iguape_path = os.path.join(os.path.dirname(__file__), "iguape.py")
    iguape_dir = os.path.dirname(__file__)
    os.chdir(iguape_dir)
    try:
        subprocess.run(["python", 'iguape.py'])
    except Exception as e:
        subprocess.run(["python3", 'iguape.py'])


if __name__=='__main__':
    main()

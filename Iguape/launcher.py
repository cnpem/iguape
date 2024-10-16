# Iguape/launcher.py

import subprocess
import os


def main():
    # Obtém o caminho completo do arquivo iguape.py
    iguape_path = os.path.join(os.path.dirname(__file__), "iguape.py")
    iguape_dir = os.path.dirname(__file__)
    os.chdir(iguape_dir)
# Executa o arquivo iguape.py via subprocess
    subprocess.run(["python3", 'iguape.py'])

if __name__=='__main__':
    main()
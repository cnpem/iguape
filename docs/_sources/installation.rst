Installation Guide
==================

Welcome to the installation guide for Iguape! Follow the instructions below to install the software on your preferred operating system.

Iguape requires **Python 3.10** or higher. Please ensure you have the correct version installed before proceeding.

Linux and macOS
---------------

On Linux and macOS, Iguape can be installed via the command line. Follow these steps:

.. code-block:: bash

   # Verify Python version
   python3 --version

If you see a version lower than Python 3.10, update it.

After ensuring Python 3.10 or higher is installed, proceed with installing Iguape:

.. code-block:: bash

   pip install iguape

To verify the installation, you can run:

.. code-block:: bash

   iguape

It's always better to setup a python environment before installing any package. If you are familiar with Anaconda, you can create a conda environment (with python 3.10 or higher)
and then install iguape via pip.

.. code-block:: bash

   conda env create -n iguape-env python=3.11
   conda activate iguape-env
   pip install iguape
   iguape

Alternatively you can write a `environment.yml` file:

.. code-block:: yaml

   name: iguape-env
   channels: 
      - conda-forge
   dependencies:
      - python = 3.11
      - pip:
         - iguape

And then, run in your conda prompt (or base environment):

.. code-block:: bash
   conda env create --file environment.yml

Windows
-------

To install Iguape on Windows, ensure you have **Python 3.10** or higher:

1. Download Python 3.10 - `Python webpage <https://www.python.org/downloads/>`_.
2. Follow the installation instructions, making sure to select "Add Python to PATH."

Once Python 3.10 is set up, download the installer for Iguape from the following link:

- `Windows Installer <https://github.com/cnpem/iguape/releases/>`_

After downloading, double-click the installer and follow the on-screen instructions.

To verify the installation, there is a test dataset available at the following link: `Test Data <_static/iguape_test_dataset.zip>`_

We also make available a tutorial showing the most important features of Iguape: `Tutorial <_static/Iguape_Tutorial.pptx>`_
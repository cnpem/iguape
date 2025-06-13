.. Iguape - Paineira Graphical User Interface documentation master file, created by
   sphinx-quickstart on Sun Oct 27 16:32:52 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Iguape - Paineira Graphical User Interface documentation
========================================================
This page is serves as a a documentation and tutorial for Iguape. This program was desinged to read data acquired at Paineira, and does not support data from other sources. 
However, it is possible to change the Monitor class, found in the soruce code, to support other data sources. 
Beware that this program is under the GNU General Public License v3.0, and any changes made to the source code must be shared with the community. 

You can find the source code for Iguape at the CNPEM GitHub Page: `Iguape Source Code <https://github.com/cnpem/iguape>`_

Paineira Web-Site is found at: `Paineira <https://lnls.cnpem.br/facilities/paineira/>`_

LNLS Web-Site is found at: `LNLS <https://lnls.cnpem.br/>`_

If IGUAPE has been useful in your reasearch, please, consider citing:

Biondo Neto, J. L., Cintra Mauricio, J. & Rodella, C. B. (2025). \n J. Appl. Cryst. 58, 1061-1067. **DOI**: https://doi.org/10.1107/S1600576725003309

.. code-block:: bibtex

   @article{BiondoNeto:yr5153,
      author = "Biondo Neto, Jo{\~{a}}o L. and Cintra Mauricio, Junior and Rodella, Cristiane B.",
      title = "{{\it IGUAPE}, a graphical user interface for {\it in situ/operando} X-ray diffraction experiments at the PAINEIRA beamline: development and application}",
      journal = "Journal of Applied Crystallography",
      year = "2025",
      volume = "58",
      number = "3",
      pages = "1061--1067",
      month = "Jun",
      doi = {10.1107/S1600576725003309},
      url = {https://doi.org/10.1107/S1600576725003309},
      abstract = {Synchrotron radiation X-ray diffraction facilities equipped with fast area detectors can generate X-ray diffraction (XRD) patterns in seconds. This capability is fundamental to revealing transient crystalline phases and the structural evolution of samples and devices for technology applications. However, it generates XRD patterns usually faster than the user can process during the experiment. Thus, an open-source and user-friendly software package named {\it IGUAPE} was developed for the PAINEIRA beamline (Sirius, Brazil). It allows visualization of the X-ray diffractograms as soon as the azimuthal integration of the Debye rings is processed and the XRD pattern is created. The software can also perform a single-peak qualitative analysis of the diffraction data. Upon selecting a diffraction peak in the XRD pattern, the peak position, integrated area and full width at half-maximum variation during the {\it in situ} or {\it operando} experiment are given.},
      keywords = {open-source software, <it>IGUAPE</it>, X-ray diffraction, XRD, PAINEIRA beamline, <it>in situ</it> experiments},
   }



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   modules
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
import os  # numpydoc ignore=GL08
from qtpy.QtCore import Signal, QObject, Slot
from .utils.utils import counter
from .models.xrd import XRDMetadataPNR
from .protocols.readers import PNRXRDReader
import logging

logger = logging.getLogger(__name__)


class FolderMonitor(QObject):
    """This class is designed to work only with data obtained at the PNR beamline (LNLS-Sirius).

    It will look for "iguape_filelist.txt" inside the passed repo and load the data to `PNRXRDReader`.
    This object is emited, and it is meant to be consumed by the GUI client.

    Parameters
    ----------
    folder_path : str
        Path to the folder where the data is stored.
    parent : optional
        `QObject`'s parent.
    """

    data = Signal(PNRXRDReader)
    finished = Signal()

    def __init__(self, folder_path: str, parent=None):  # numpydoc ignore=GL08
        super().__init__(parent)
        self._folder_path = folder_path

    @Slot()
    def run(self):
        """Start the worker. This is designed to work only with data obtained at the PNR beamline."""
        os.system("cls" if os.name == "nt" else "clear")
        reading_status = 1
        i = 0
        logger.info(f"Monitoring folder: {self.folder_path}")
        logger.info("Waiting for XRD data! Please, wait")
        file_index = counter()
        while reading_status == 1:
            while True:
                try:
                    with open(
                        os.path.join(self.folder_path, "iguape_filelist.txt"), "r"
                    ) as file:
                        lines = file.read().splitlines()
                        line = lines[i + 1]
                        self.data.emit(
                            PNRXRDReader(
                                XRDMetadataPNR(
                                    file_path=os.path.join(self.folder_path, line),
                                    file_index=next(file_index),
                                )
                            )
                        )
                        logger.info(
                            f"New data created at: {self.folder_path}. File name: {lines[i + 1]}"
                        )

                        reading_status = int(lines[i + 2])
                    break
                except Exception as e:
                    raise Exception(f"{e}") from e

            i += 2

        file_index.close()
        self.finished.emit()

    @property
    def folder_path(self):
        """`folder_path` read-only property.

        Returns
        -------
        str
            Path to folder being monitored.
        """
        return self._folder_path

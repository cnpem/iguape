from abc import ABC, abstractmethod
from ..models.xrd import (
    XRDMetadataPNR,
    BaseXRDPattern,
    XRDMetadataBaseClass,
    PNRTemperatureUnit,
)
import pandas as pd
import polars as pl


class IXRDReader(ABC):
    """Interface for XRD file readers"""

    def __init__(self, metadata: XRDMetadataBaseClass):
        self.metadata = metadata

    @property
    def file_path(self):
        return self.metadata.file_path

    @property
    def file_index(self):
        return self.metadata.file_index

    @abstractmethod
    def read_data(self) -> BaseXRDPattern:
        """This function should be responsible for reading the file given in the `file_path` property"""
        raise NotImplementedError


class PNRReader(IXRDReader):
    metadata: XRDMetadataPNR

    def __init__(self, metadata: XRDMetadataPNR):
        super().__init__(metadata)

    def read_data(self):
        try:
            data = pl.read_csv(self.file_path, separator=",", comment_prefix="#")
            x = data.to_numpy()[:, 0]
            y = data.to_numpy()[:, 1]
            file_name = self.file_path.split(sep="/")[
                len(self.file_path.split(sep="/")) - 1
            ]
            temp = None
            for i in file_name.split(sep="_"):
                if "Celsius" in i:
                    temp = float(i.split(sep="Celsius")[0])  # Getting the temperature
                    temp_unit = PNRTemperatureUnit.CELSIUS
                elif "Kelvin" in i:
                    temp = float(i.split(sep="Kelvin")[0])
                    temp_unit = PNRTemperatureUnit.KELVIN

            if temp is not None:
                self.metadata.temperature = temp
                self.metadata.temperature_unit = temp_unit

            return BaseXRDPattern(x_data=x, y_data=y)

        except pd.errors.EmptyDataError as err:
            raise pd.errors.EmptyDataError(
                f"Warning: Empty file encountered: {self.file_path}!"
            ) from err

        except Exception as err:
            raise Exception(f"An error occurred while reading data: {err}!") from err

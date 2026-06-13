from typing import Annotated, Any
from enum import StrEnum, Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator, BeforeValidator
import numpy.typing as npt
import numpy as np


class PNRTemperatureUnit(StrEnum):
    CELSIUS = "°C"
    KELVIN = "K"


class PNRTemperatureValidationError(ValueError):
    def __init__(self, temperature):
        super().__init__(
            f"Temperature {temperature} is given, but no unit was provided."
        )


class PNRTemperatureUnitValidationError(ValueError):
    def __init__(self, temperature_unit):
        super().__init__(
            f"Temperature unit {temperature_unit} was given but no temperature was provided."
        )


class XRDMetadataBaseClass(BaseModel):
    model_config = ConfigDict(extra="allow")
    file_path: Annotated[
        str,
        Field(
            description="The path for XRD file. This will be used by IGUAPE to read the data on demand."
        ),
    ]
    file_index: Annotated[
        int,
        Field(
            description="The index of the XRD file. This can be used to sorted the plotting and to identify each XRD pattern."
        ),
    ]

    extra_md: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Optional metadata in the form of a python `dictionary`.",
        ),
    ]


class XRDMetadataPNR(XRDMetadataBaseClass):
    source: Annotated[str, Field(default="PNR", frozen=True)]

    temperature: Annotated[
        float | None,
        Field(
            default=None,
            description="Optional value for the temperature in which the XRD pattern was cllected. ",
        ),
    ]
    temperature_unit: Annotated[
        PNRTemperatureUnit | None,
        Field(
            default=None,
            description="Optional unit for the temperature given in the `temperature` field.",
        ),
    ]

    @model_validator(mode="after")
    def _validate_temperature_and_unit(self) -> "XRDMetadataBaseClass":
        if self.temperature is not None and self.temperature_unit is None:
            raise PNRTemperatureValidationError(self.temperature)
        elif self.temperature is None and self.temperature_unit is not None:
            raise PNRTemperatureUnitValidationError(self.temperature_unit)

        return self


class XRDIndependentVar(Enum):
    """Possible independent variable as a tuple: (label, unit)."""

    TWO_THETA = ("Two-Theta", "degrees")
    SCATTERING_VECTOR = ("Scattering Vector (q)", "Å⁻¹")
    D_SPACING = ("d-spacing", "Å")

    def __init__(self, label: str, unit: str):
        self.label = label
        self.unit = unit


class XRDDependentVar(Enum):
    COUNTS = ("Counts", "counts")
    ARBRITRARY_UNITS = ("Arbritrary Units", "a.u.")

    def __init__(self, label: str, unit: str):
        self.label = label
        self.unit = unit


def validate_1d_numeric_array(v: Any) -> npt.NDArray[np.float64]:
    """Ensures the input is converted into a 1D numpy array of floats."""
    try:
        # Convert to numpy array if it isn't one already
        array = np.asarray(v, dtype=np.float64)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Could not convert input to a numeric numpy array: {e}")

    if array.ndim != 1:
        raise ValueError(f"XRD data must be a 1D array, got {array.ndim}D instead.")

    return array


XRDArray = Annotated[
    npt.NDArray[np.float64], BeforeValidator(validate_1d_numeric_array)
]


class BaseXRDPattern(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    x_data: Annotated[
        XRDArray, Field(description="Indenpent variable for the XRD pattern.")
    ]
    y_data: Annotated[
        XRDArray, Field(description="Dependent variable for the XRD pattern.")
    ]
    x_data_type: Annotated[
        XRDIndependentVar,
        Field(
            default=XRDIndependentVar.TWO_THETA,
            description="Type of independent variable for XRD patterns. It can be one of the `XRDIndependentVar` enum.",
        ),
    ]
    y_data_type: Annotated[
        XRDDependentVar,
        Field(
            default=XRDDependentVar.ARBRITRARY_UNITS,
            description="Type of dependent variable for XRD patterns. It can be one of the `XRDDependentVar` enum.",
        ),
    ]

    @model_validator(mode="after")
    def _validate_x_and_y_shapes(self) -> "BaseXRDPattern":
        x_shape = self.x_data.shape
        y_shape = self.y_data.shape
        if x_shape != y_shape:
            raise ValueError(
                f"The x_data array shape {x_shape} doesn't match the y_data array shape {y_shape}."
            )
        return self

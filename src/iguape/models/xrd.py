from typing import Annotated, Any
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TemperatureUnit(StrEnum):
    CELSIUS = "°C"
    FAHRENHEIT = "F"
    KELVIN = "K"


class TemperatureValidationError(ValueError):
    def __init__(self, temperature):
        super().__init__(
            f"Temperature {temperature} is given, but no unit was provided."
        )


class TemperatureUnitValidationError(ValueError):
    def __init__(self, temperature_unit):
        super().__init__(
            f"Temperature unit {temperature_unit} was given but no temperature was provided."
        )


class XRDMetadataBaseClass(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    temperature: Annotated[
        float | None,
        Field(
            default=None,
            description="Optional value for the temperature in which the XRD pattern was cllected. ",
        ),
    ]
    temperature_unit: Annotated[
        TemperatureUnit | None,
        Field(
            default=None,
            description="Optional unit for the temperature given in the `temperature` field.",
        ),
    ]
    source: Annotated[
        str | None,
        Field(
            default=None,
            description="Source of the XRD measure. This can be either the Beamline, or equipment from which it was measured.",
        ),
    ]
    extra_md: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description="Optional metadata in the form of a python `dictionary`.",
        ),
    ]

    @model_validator(mode="after")
    def _validate_temperature_and_unit(self) -> "XRDMetadataBaseClass":
        if self.temperature is not None and self.temperature_unit is None:
            raise TemperatureValidationError(self.temperature)
        elif self.temperature is None and self.temperature_unit is not None:
            raise TemperatureUnitValidationError(self.temperature_unit)

        return self

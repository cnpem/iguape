from pydantic import BaseModel, Field
from enum import StrEnum
from typing import Literal, List


class PeakProfile(StrEnum):
    PSD_VOIGT = "PseudoVoigt"
    VOIGT = "Voigt"
    GAUSSIAN = "Gaussian"
    LORENTZIAN = "Lorentzian"
    DOUBLE_PSD_VOIGT = "DoublePseudoVoigt"


class PeakFitResult(BaseModel):
    """Core attributes that every single-peak fit result must possess."""

    center: float = Field(..., description="The peak position")
    height: float = Field(..., description="The maximum intensity/height of the peak.")
    fwhm: float = Field(..., description="Full Width at Half Maximum.")
    area: float = Field(..., description="Calculated integrated area under the peak.")
    r_squared: float = Field(
        ..., description="Goodness of fit (R²) for this specific peak."
    )


class GaussianFit(PeakFitResult):
    profile_type: Literal[PeakProfile.GAUSSIAN] = PeakProfile.GAUSSIAN
    sigma: float = Field(
        ..., description="Standard deviation parameter for Gaussian distribution."
    )


class LorentzianFit(PeakFitResult):
    profile_type: Literal[PeakProfile.LORENTZIAN] = PeakProfile.LORENTZIAN
    gamma: float = Field(
        ..., description="Scale parameter representing half-width at half-maximum."
    )


class VoigtFit(PeakFitResult):
    profile_type: Literal[PeakProfile.VOIGT] = PeakProfile.VOIGT
    sigma: float = Field(..., description="Gaussian component width.")
    gamma: float = Field(..., description="Lorentzian component width.")


class PseudoVoigtFit(PeakFitResult):
    profile_type: Literal[PeakProfile.PSD_VOIGT] = PeakProfile.PSD_VOIGT
    fraction_eta: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mixing profile parameter (1.0 = pure Lorentzian, 0.0 = pure Gaussian).",
    )


class CompositePseudoVoigtFit(PeakFitResult):
    profile_type: str = Field(..., description="Peak profile.")

    peaks: List[PseudoVoigtFit] = Field(
        ...,
        min_items=2,
        description="List of PseudoVoigt peak fits in the composition profile. ",
    )
    num_peaks: int = Literal[len(peaks)]

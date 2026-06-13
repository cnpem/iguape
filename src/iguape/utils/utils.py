import numpy as np
import math


def counter():
    i = 1
    while True:
        yield i
        i += 1


def calculate_q_vector(wavelength: float, two_theta: np.ndarray):
    r"""
    Converts 2theta values into Q vector (Scattering vector).
            .. math::
                    Q = \frac{4\pi}{\lambda} \sin{\theta}

    :param wavelength: wavelength in Angstroms
    :type wavelength: float
    :param two_theta: 2theta values array
    :type two_theta: np.ndarray
    :return: Q-vector
    :rtype: Q-vector values array
    """
    return (4 * np.pi / wavelength) * np.sin(np.deg2rad(two_theta / 2))


def normalize_array(array: np.array):
    """
    Normalizes (by the maximum) and array

    :param array: Array to be normalized
    :type array: np.array
    :return: Normalized (by maximum) array
    :rtype: np.array
    """
    return array / np.max(array)


def pseudo_voigt(x, amplitude, center, sigma, eta):
    r"""
    PseudoVoigt function, a linear combination of a Gaussian and a Lorentzian function.

    Parameters
    ----------
            x (np.array): 2theta array.
            amplitude (float): Peak amplitude.
            center (float): Peak center.
            sigma (float): Sigma value or standard deviation.
            eta (float): Eta value (mixing parameter).

    Returns
    -------
            np.array: PseudoVoigt function.

    Notes
    -----
    The PseudoVoigt function is defined as:
            .. math::
                    PV(x; A, \mu, \sigma, \eta) = \eta L(x; A, \mu, \sigma) + (1 - \eta) G(x; A, \mu, \sigma)
            .. math::
                    L(x; A, \mu, \sigma) = \frac{A}{\pi} \left[ \frac{\sigma}{(x-\mu)^2 + \sigma^{2}} \right]
            .. math::
                    G(x; A, \mu, \sigma) = \frac{A}{\sigma\sqrt{2\pi}}e^{\left[ \frac{-(x - \mu)^{2}}{2\sigma^{2}} \right]}
    """
    sigma_g = sigma / math.sqrt(2 * math.log(2))
    gaussian = (amplitude / (sigma_g * math.sqrt(2 * math.pi))) * np.exp(
        -((x - center) ** 2) / (2 * sigma_g**2)
    )
    lorentzian = ((amplitude / math.pi) * sigma) / ((x - center) ** 2 + sigma**2)
    return eta * lorentzian + (1 - eta) * gaussian


def split_pseudo_voigt(x, amp1, cen1, sigma1, eta1, amp2, cen2, sigma2, eta2):
    r"""
    Split PseudoVoigt function, a linear combination of two PseudoVoigt functions.

    :param x: 2theta array
    :type x: np.array
    :param amp1: Peak amplitude for the first peak
    :type amp1: np.array
    :param cen1: Peak center for the first peak.
    :type cen1: float
    :param sigma1: Sigma value or standard deviation for the first peak.
    :type sigma1: float
    :param eta1: Eta value for the first peak (mixing parameter).
    :type eta1: float
    :param amp2: Peak amplitude for the second peak.
    :type amp2: float
    :param cen2: Peak center for the second peak.
    :type cen2: float
    :param sigma2: Sigma value or standard deviation for the second peak.
    :type sigma2: float
    :param eta2: Eta value for the second peak (mixing parameter).
    :type eta2: float
    :return: Split PseudoVoigt function
    :rtype: np.array

    Notes
            -----
            The Split PseudoVoigt function is defined as:
                    .. math::
                            SPV(x; A1, \mu1, \sigma1, \eta1, A2, \mu2, \sigma2, \eta2) = PV1(x; A1, \mu1, \sigma1, \eta1) + PV2(x; A2, \mu2, \sigma2, \eta2)
    """
    return pseudo_voigt(
        x, amplitude=amp1, center=cen1, sigma=sigma1, eta=eta1
    ) + pseudo_voigt(x, amplitude=amp2, center=cen2, sigma=sigma2, eta=eta2)

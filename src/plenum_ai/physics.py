"""Small deterministic physics demonstration, not a general purpose simulator."""
from math import isfinite, sqrt

GRAVITATIONAL_CONSTANT = 6.67430e-11
EARTH_MASS_KG = 5.9722e24


def circular_orbit_speed(radius_m, central_mass_kg=EARTH_MASS_KG):
    if not (isfinite(radius_m) and isfinite(central_mass_kg)):
        raise ValueError("Input must be finite")
    if radius_m <= 0 or central_mass_kg <= 0:
        raise ValueError("Radius and mass must be positive")
    return sqrt(GRAVITATIONAL_CONSTANT * central_mass_kg / radius_m)

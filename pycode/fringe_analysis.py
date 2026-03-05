import numpy as np
import scipy.fft as fft

class FringeAnalyzer:
    """
    Generalized script for fringe analysis targeting both Planar and Radial geometries.
    Refactoring ideas from Lab 1 (Planar) and Lab 2 (Radial/Spherical).
    """
    def __init__(self, image_data):
        self.image = np.array(image_data)
        self.height, self.width = self.image.shape
        
    def planar_fft(self):
        """
        Performs 1D/2D FFT suitable for planar Mach-Zehnder fringes.
        """
        # Collapse along the y-axis if fringes are vertical
        profile_1d = np.mean(self.image, axis=0)
        
        # Simple windowing
        window = np.hanning(len(profile_1d))
        profile_windowed = profile_1d * window
        
        freqs = fft.fftfreq(len(profile_1d))
        spectrum = np.abs(fft.fft(profile_windowed))
        
        return freqs, spectrum

    def radial_fft(self, center_guess=None):
        """
        Performs analysis for radial fringes (e.g., from Spherical lenses in MZI, 
        or Michelson setup). Finds center, extracts radial profile, then applies FFT/peak finding.
        """
        if center_guess is None:
            # Default to center of image
            center_guess = (self.width // 2, self.height // 2)
            
        cx, cy = center_guess
        y, x = np.indices(self.image.shape)
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Bin pixels by radius to get a radial profile
        r_int = np.round(r).astype(int)
        tbin = np.bincount(r_int.ravel(), self.image.ravel())
        nr = np.bincount(r_int.ravel())
        radial_profile = tbin / np.maximum(nr, 1) # Avoid div by zero
        
        # Optional: detrend or FFT the 1D radial profile to find fringe spacing
        return radial_profile

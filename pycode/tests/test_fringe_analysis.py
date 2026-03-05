import pytest
import numpy as np
import sys
import os

# Add parent directory to path to import local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fringe_analysis import FringeAnalyzer

def test_planar_fft():
    # Create dummy 100x100 image with horizontal fringes
    y, x = np.indices((100, 100))
    image = np.sin(x * 0.5) 
    
    analyzer = FringeAnalyzer(image)
    freqs, spectrum = analyzer.planar_fft()
    
    assert len(freqs) == 100
    assert len(spectrum) == 100

def test_radial_fft():
    # Create dummy 100x100 image with radial fringes
    y, x = np.indices((100, 100))
    r = np.sqrt((x - 50)**2 + (y - 50)**2)
    image = np.cos(r * 0.5)
    
    analyzer = FringeAnalyzer(image)
    radial_prof = analyzer.radial_fft()
    
    assert len(radial_prof) > 0

import pytest
import sys
import os

# Add parent directory to path to import local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathway_algorithms import PathExtractor

def test_calibration():
    extractor = PathExtractor()
    px_per_cm = extractor.calibrate_from_ruler((0,0), (100,0), 10.0)
    assert px_per_cm == 10.0

def test_extract_optical_path():
    extractor = PathExtractor(calibration_px_per_cm=10.0)
    nodes = [(0, 0), (100, 0), (100, 50)]
    
    dist_cm = extractor.extract_optical_path(*nodes)
    assert dist_cm == 15.0 # (100 pixels + 50 pixels) / 10 px/cm

def test_extract_without_calibraton():
    extractor = PathExtractor()
    with pytest.raises(ValueError):
        extractor.extract_optical_path((0,0), (100,100))

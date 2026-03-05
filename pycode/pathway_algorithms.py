import numpy as np

class PathExtractor:
    """
    Refactored class tracking optical pathways and ruler extraction logic.
    Generalizes pixel-to-metric conversions based on Lab 2's CV pipeline logic.
    """
    def __init__(self, calibration_px_per_cm=None):
        self.px_per_cm = calibration_px_per_cm

    def calibrate_from_ruler(self, ruler_start_px, ruler_end_px, known_length_cm):
        """
        Calibrates the pixel-to-cm ratio based on ruler start/end pixel coordinates.
        """
        dist_px = np.linalg.norm(np.array(ruler_end_px) - np.array(ruler_start_px))
        self.px_per_cm = dist_px / known_length_cm
        return self.px_per_cm

    def extract_optical_path(self, *nodes):
        """
        Given a list of node tuples (x, y) extending throughout an optical sequence,
        computes the physical path length in cm.
        
        Requires calibration_px_per_cm to be set.
        """
        if not self.px_per_cm:
            raise ValueError("Must set or calibrate px_per_cm before extracting path length.")
            
        total_dist_px = 0.0
        for i in range(len(nodes) - 1):
            p1 = np.array(nodes[i])
            p2 = np.array(nodes[i+1])
            total_dist_px += np.linalg.norm(p2 - p1)
            
        return total_dist_px / self.px_per_cm

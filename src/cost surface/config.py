import json
import os

# --- Input rasters ---
INPUT_RASTERS = {
    "dem": "data/tif/dem.tif",                                          # meters above sea level
    "slope": "data/tif/slope.tif",                                      # degrees (0-90)
    "curvature": "data/tif/windshelter.tif",                            # curvature (-1, 1), (from "ridges" to "bowls")
    "travel_angle": "data/flow-py_outputs/tif/FP_travel_angle.tif"      # degrees (0-180)
}

# --- Masks (0/1), same shape as input rasters ---
MASK_RASTERS = {
    "roads": "data/tif/roads.tif",                                      # 1 where roads
    "tractorroads_trails": "data/tif/tractorroads_trails.tif",          # 1 where tractor roads or trails
    "rivers": "data/tif/rivers.tif"                                     # 1 where rivers
}

# --- Reference raster (for shape/projection) ---
REF_RASTER = INPUT_RASTERS["slope"]

# --- Weights for SUM-based terrain-cost-surface ---
WEIGHTS_TERRAIN = {
    "slope": 0.5,
    "curvature": 0.1,
    "travel_angle": 0.4
}

# --- Transform parameters (generalized Cauchy) ---
TRANSFORM_PARAMS = {   'curvature': {'a': 3, 'b': 10, 'c': 3},
    'slope': {'a': 11, 'b': 4, 'c': 43},
    'travel_angle': {'a': 4.5, 'b': 1, 'c': 43}}

# --- Slider ranges for UI ---
PARAM_RANGES = {
    "a": (0, 90),
    "b": (0.1, 11),
    "c": (0, 180)
}

MIN_COST = 1
MAX_COST = 99

# --- Constants ---
BARRIER_VALUE = 99.0
ROADS_MIN_VALUE = 2.0
# ROADS_ELSEWHERE_VALUE = 99.0

OUTPUT_COST = "output/cost_surface.tif"
NODATA_VALUE = 255

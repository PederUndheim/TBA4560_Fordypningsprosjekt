import json
import os

# --- Input rasters ---
INPUT_RASTERS = {
    "dem": "data/tif/dem.tif",                                              # meters above sea level
    "slope": "data/tif/slope.tif",                                          # degrees (0-90)
    "curvature": "data/tif/windshelter.tif",                                # curvature (-1, 1), (from "ridges" to "bowls")
    "pra_runout_combined": "data/tif/pra_runout_combined.tif",              # avalance cost raster with runoout (1-7.2) and release (7.2-99)
}

# --- Masks (0/1), same shape as input rasters ---
MASK_RASTERS = {
    "roads": "data/tif/roads.tif",                                          # 1 where roads
    "tractorroads_trails": "data/tif/tractorroads_trails_in_forest.tif",    # 1 where tractor roads or trails
    "rivers": "data/tif/river.tif",                                         # 1 where rivers
    "bridges": "data/tif/bridge.tif",                                       # 1 where bridges
    "fake_bridge": "data/tif/fake_bridge.tif"                               # 1 where fake bridge
}

# --- Reference raster (for shape/projection) ---
REF_RASTER = INPUT_RASTERS["slope"]

# --- Weights for SUM-based terrain-cost-surface ---
WEIGHTS_TERRAIN = {
    "slope": 6,
    "curvature": 1,
    "pra_runout_combined": 4
}

# --- Transform parameters  ---
TRANSFORM_PARAMS = {   
    'curvature': {'x0': 0.0, 'k': 5.5},
    'slope': {'x0': 41, 'k': 0.6}
}

MIN_COST = 1
MAX_COST = 99

# --- Constants ---
BARRIER_VALUE = 99.0
ROADS_MIN_VALUE = 2.0
# ROADS_ELSEWHERE_VALUE = 99.0

OUTPUT_COST = "output/cost_surface.tif"
NODATA_VALUE = 255
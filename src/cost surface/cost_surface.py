import rasterio
import numpy as np
import os

import config
from transforms import (
    slope_cost, 
    curvature_cost,
    travel_angle_cost,
    barrier_layer_from_mask,
    reduction_layer_from_mask,
)
from combine import compute_surface_cost, clip_round

np.seterr(all='ignore')  # ignore warnings for NaNs

def _read_raster(path: str) -> tuple[np.ndarray, dict]:
    """Read raster as float32, propagate nodata as np.nan."""
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile
        nodata = src.nodata
    arr = arr.astype(np.float32, copy=False)
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr, profile

def _read_mask(path: str) -> np.ndarray:
    """Return boolean mask (True where feature exists)."""
    with rasterio.open(path) as src:
        band = src.read(1)
        nodata = src.nodata
    if nodata is not None:
        band = np.where(band == nodata, 0, band)
    return (band != 0)

def create_cost_surface(output_path: str | None = None):
    output_path = output_path or config.OUTPUT_COST

    # Reference profile
    with rasterio.open(config.REF_RASTER) as ref:
        ref_profile = ref.profile

    # Load input rasters
    dem_arr, _ = _read_raster(config.INPUT_RASTERS["dem"])
    slope_arr, _ = _read_raster(config.INPUT_RASTERS["slope"])
    curvature_arr, _ = _read_raster(config.INPUT_RASTERS["curvature"])
    travel_angle_arr, _ = _read_raster(config.INPUT_RASTERS["travel_angle"])

    # Verify shapes
    for arr in [curvature_arr, travel_angle_arr]:
        if arr.shape != slope_arr.shape:
            raise ValueError("Input rasters must have the same shape")

    # Handle nodata as MIN_COST
    travel_angle_arr = np.nan_to_num(travel_angle_arr, nan=100)

    # Terrain transforms using generalized Cauchy
    slope_cost_arr = slope_cost(slope_arr, **config.TRANSFORM_PARAMS["slope"])
    curvature_cost_arr = curvature_cost(curvature_arr, **config.TRANSFORM_PARAMS["curvature"])
    travel_angle_cost_arr = travel_angle_cost(travel_angle_arr, **config.TRANSFORM_PARAMS["travel_angle"])

    # Mask layers
    rivers_mask = _read_mask(config.MASK_RASTERS["rivers"]) if config.MASK_RASTERS.get("rivers") else None
    roads_mask = _read_mask(config.MASK_RASTERS["roads"]) if config.MASK_RASTERS.get("roads") else None
    tractorroads_trails_mask = _read_mask(config.MASK_RASTERS.get("tractorroads_trails")) if config.MASK_RASTERS.get("tractorroads_trails") else None

    # Barrier / reduction layers
    rivers_barrier = barrier_layer_from_mask(rivers_mask, barrier_value=config.BARRIER_VALUE) if rivers_mask is not None else None
    roads_reduction = reduction_layer_from_mask(roads_mask, dem=dem_arr, low_value=config.ROADS_MIN_VALUE, elsewhere_value=config.BARRIER_VALUE) if roads_mask is not None else None
    tractorroads_trails_reduction = reduction_layer_from_mask(tractorroads_trails_mask, dem=dem_arr, low_value=config.ROADS_MIN_VALUE, elsewhere_value=config.BARRIER_VALUE) if tractorroads_trails_mask is not None else None

    # Combine layers: weighted sum -> MAX barrier -> MIN reductions
    surface_f32 = compute_surface_cost(
        slope=slope_cost_arr,
        curvature=curvature_cost_arr,
        travel_angle=travel_angle_cost_arr,
        roads_reduction=roads_reduction,
        tractorroads_trails_reduction=tractorroads_trails_reduction,
        rivers_barrier=rivers_barrier,
        weights=config.WEIGHTS_TERRAIN,
        min_cost=1.0,
        max_cost=99.0,
    )

    # Propagate nodata
    nodata_mask = np.isnan(slope_arr) | np.isnan(curvature_arr) | np.isnan(travel_angle_arr)
    surface_u8 = clip_round(surface_f32, min_cost=1.0, max_cost=99.0)
    surface_u8[nodata_mask] = config.NODATA_VALUE

    # Write output raster
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prof = ref_profile.copy()
    prof.update(dtype=rasterio.uint8, count=1, compress='lzw', nodata=config.NODATA_VALUE)
    with rasterio.open(output_path, 'w', **prof) as dst:
        dst.write(surface_u8, 1)

    print(f"Cost surface written to {output_path}")


if __name__ == "__main__":
    create_cost_surface()

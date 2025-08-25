import rasterio
import numpy as np
import os

from transforms import slope_cost, forest_cost
from combine import weighetd_sum, apply_barriers, apply_reductions
import config

TRANSFORM_FUNCS = {
    "slope": slope_cost,
    "forest": forest_cost,
}

def create_cost_surface(output_path):
    # Reference raster: first in config
    ref_path = next(iter(config.INPUT_RASTERS.values()))
    with rasterio.open(ref_path) as ref:
        profile = ref.profile
        height, width = ref.height, ref.width

    # Apply transforms
    cost_layers = {}
    for name, path in config.INPUT_RASTERS.items():
        with rasterio.open(path) as src:
            raw = src.read(1).astype(np.float32)
            transform_fn = TRANSFORM_FUNCS[name]
            cost_layers[name] = transform_fn(raw)

    # Weighted sum
    cost_surface = weighetd_sum(cost_layers, config.WEIGHTS)

    # Apply barriers
    for name, path in config.BARRIERS.items():
        with rasterio.open(path) as src:
            mask = src.read(1).astype(bool)
            cost_surface = apply_barriers(cost_surface, mask)

    # Apply reductions
    for name, path in config.REDUCTIONS.items():
        with rasterio.open(path) as src:
            mask = src.read(1).astype(bool)
            cost_surface = apply_reductions(cost_surface, mask)

    # Finalize output
    final_cost = np.round(np.clip(cost_surface, 1, 99)).astype(np.uint8)
    final_cost[np.isnan(cost_surface)] = 255 # set nodata
    profile.update(dtype=rasterio.uint8, count=1, compress='lzw', nodata=255)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(final_cost, 1)
    
    print(f"Cost surface written to {output_path}")


if __name__ == "__main__":
    create_cost_surface("output/cost_surface.tif")

import rasterio
import numpy as np

# --- Inputs ---
tractorroads_trails_path = "data/tif/tractorroads_trails.tif"       # 1 where tractor roads or trails
forest_path      = "data/tif/number_of_stems_ha.tif"                   # Forest (enough stems) where value > 0
output_path       = "data/tif/tractorroads_trails_in_forest.tif"    # output path


OUTPUT_NODATA = -9999.0


with rasterio.open(tractorroads_trails_path) as tt_src, \
     rasterio.open(forest_path)      as for_src:
    
    tractorroads_trails = tt_src.read(1)
    forest      = for_src.read(1)

    # Start with all NoData
    out = np.full(tractorroads_trails.shape, OUTPUT_NODATA, dtype=np.float32)
    
    # Get value of the tractor roads/trails where forest not NoData
    mask = (forest > 0)
    out[mask] = tractorroads_trails[mask]

    # Write output (copy georeferencing from PRA_raw)
    meta = tt_src.meta.copy()
    meta.update(dtype="float32", count=1, compress="lzw", nodata=OUTPUT_NODATA)

    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(out, 1)

print("Raster saved:", output_path)

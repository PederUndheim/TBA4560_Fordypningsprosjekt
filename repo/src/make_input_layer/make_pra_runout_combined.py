import rasterio
import numpy as np

# --- Inputs ---
travel_distance_path = "data/tif/FP_travel_distance.tif"   # values for travel distance in meters. ca 0-1200. 10 000 where too far away. 0 where PRA
pra_raw_path      = "data/tif/PRA_raw.tif"                 # values from 0 to 1. Higher = more likely to release
output_path       = "data/tif/pra_runout_combined.tif"

# Target ranges
RUNOUT_MIN, RUNOUT_MAX   = 1.0, 7.2
RELEASE_MIN, RELEASE_MAX = 7.2, 99.0

OUTPUT_NODATA = -9999.0

# Parameters to weibull-fit for travel distance danger
LAMBDA = 0.016   # m^-1
ALPHAW = 0.82    # shape param

def linear_rescale_on_mask(src, mask, in_min, in_max, out_min, out_max):
    """Linearly rescale values of src on mask from [in_min,in_max] → [out_min,out_max]."""
    out = src.astype(np.float32, copy=True)
    if not np.any(mask): return out
    rng = float(in_max - in_min)
    if rng <= 0:
        out[mask] = np.float32(0.5 * (out_min + out_max))
        return out
    v = np.clip(src, in_min, in_max)
    scaled = (v - in_min) / rng
    out_vals = out_min + scaled * (out_max - out_min)
    out[mask] = out_vals[mask].astype(np.float32)
    return out



with rasterio.open(travel_distance_path) as td_src, \
     rasterio.open(pra_raw_path) as pra_src:

    distance = td_src.read(1).astype(np.float32)
    pra_raw  = pra_src.read(1).astype(np.float32)

    # Initialize output with NoData
    out = np.full(distance.shape, OUTPUT_NODATA, dtype=np.float32)

    # --- Masks ---
    is_release = (pra_raw >= 0.15)
    is_runout  = (~is_release) & (distance < 10000) & (distance > 0)

    # --- RELEASE: PRA [0.15..0.99] → [7.2..99]
    release_scaled = linear_rescale_on_mask(pra_raw, is_release, 0.15, 0.99, RELEASE_MIN, RELEASE_MAX)
    out[is_release] = release_scaled[is_release]

    # --- RUNOUT: f(x) then [0..0.99] → [1.0..7.2]
    fx = np.exp(-np.power(LAMBDA * distance.astype(np.float64), ALPHAW)).astype(np.float32)
    runout_scaled = linear_rescale_on_mask(fx, is_runout, 0.0, 0.99, RUNOUT_MIN, RUNOUT_MAX)
    out[is_runout] = runout_scaled[is_runout]

    # --- Write output ---
    meta = pra_src.meta.copy()
    meta.update(dtype="float32", count=1, compress="lzw", nodata=OUTPUT_NODATA)

    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(out, 1)

print("Raster saved:", output_path)
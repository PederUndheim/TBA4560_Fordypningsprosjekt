import rasterio
import numpy as np

# --- Inputs ---
travel_angle_path = "data/tif/FP_travel_angle.tif"   # values in both release and runout. 0 where NOT runout
pra_raw_path      = "data/tif/PRA_raw.tif"           # values from 0 to 1. Higher = more likely to release
pra_binary_path   = "data/tif/PRA_binary.tif"        # 1 = release; (0 or NoData) elsewhere
output_path       = "data/tif/pra_runout_combined.tif"

# Target ranges
RUNOUT_MIN, RUNOUT_MAX   = 1.0, 7.2
RELEASE_MIN, RELEASE_MAX = 7.2, 99.0

OUTPUT_NODATA = -9999.0

def rescale_on_mask_linear(arr, mask, out_min, out_max):
    """
    Linearly rescale values of 'arr' on 'mask' to [out_min, out_max].
    Pixels not in mask are returned unchanged.
    If the masked range is degenerate (min==max), fill masked cells with midpoint.
    """
    out = arr.astype(np.float32, copy=True)
    if not np.any(mask):
        return out
    v = arr[mask].astype(np.float64)
    a_min = np.min(v)
    a_max = np.max(v)

    if a_max > a_min:
        scaled = (arr - a_min) / (a_max - a_min)
        out_vals = out_min + scaled * (out_max - out_min)
        out[mask] = out_vals[mask].astype(np.float32)
    else:
        out[mask] = np.float32(0.5 * (out_min + out_max))
    return out


def runout_scaled_cauchy(arr, mask, out_min=1.0, out_max=7.2, a=0.30, b=1.6, c=0.06, low_q=2.0, high_q=98.0):
    """
    Scale runout values using generalized Cauchy on (1 - z), with percentile min/max.
    arr:          travel_angle raster
    mask:         boolean mask for runout pixels (~is_release & travel_angle>0)
    a,b,c:        Cauchy params (smaller a or bigger b -> more values near out_max)
    low_q/high_q: robust min/max percentiles within mask
    """
    out = arr.astype(np.float32, copy=True)
    if not np.any(mask): return out

    v = arr[mask].astype(np.float64)
    lo = np.percentile(v, low_q)
    hi = np.percentile(v, high_q)
    if hi <= lo:  # degenerate case
        out[mask] = 0.5*(out_min+out_max)
        return out

    z = (arr.astype(np.float64) - lo) / (hi - lo)
    z = np.clip(z, 0.0, 1.0)

    eps = 1e-12
    g = 1.0 / (1.0 + np.abs(((1.0 - z) - c) / (a + eps))**(2.0*b))
    y = out_min + g * (out_max - out_min)
    out[mask] = y[mask].astype(np.float32)
    return out


with rasterio.open(travel_angle_path) as ta_src, \
     rasterio.open(pra_raw_path)      as pra_src, \
     rasterio.open(pra_binary_path)   as bin_src:

    travel_angle = ta_src.read(1)
    pra_raw      = pra_src.read(1)
    pra_bin      = bin_src.read(1)

    # Release where PRA_binary == 1 (treat everything else as NOT release)
    is_release = (pra_bin == 1)

    # Runout: not release AND travel_angle > 0
    is_runout = (~is_release) & (travel_angle > 0)

    # Start with all NoData
    out = np.full(travel_angle.shape, OUTPUT_NODATA, dtype=np.float32)

    # 1) Write scaled PRA_raw on release cells -> [7.2, 99]
    pra_scaled = rescale_on_mask_linear(pra_raw, is_release, RELEASE_MIN, RELEASE_MAX)
    out[is_release] = pra_scaled[is_release]

    # 2) Write scaled travel_angle on runout cells -> [1, 7.2]
    ta_scaled = runout_scaled_cauchy(travel_angle, is_runout, RUNOUT_MIN, RUNOUT_MAX)
    out[is_runout] = ta_scaled[is_runout]

    # 3) Elsewhere stays OUTPUT_NODATA (no release and travel_angle == 0)

    # Write output (copy georeferencing from PRA_raw)
    meta = pra_src.meta.copy()
    meta.update(dtype="float32", count=1, compress="lzw", nodata=OUTPUT_NODATA)

    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(out, 1)

print("Raster saved:", output_path)

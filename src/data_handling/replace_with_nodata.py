import rasterio
import numpy as np

raster = "data/flow-py_outputs/tif/FP_travel_angle_modified.tif"

target_value = 0          # value to replace
no_data_value = -9999     # NoData value

with rasterio.open(raster) as src:
    data = src.read(1)
    meta = src.meta.copy()

# Replace target values with NoData
data_modified = np.where(data == target_value, no_data_value, data)

# Update metadata to include new NoData value
meta.update(nodata=no_data_value)

# Write modified raster
with rasterio.open(raster, 'w', **meta) as dst:
    dst.write(data_modified, 1)

print("Finished. Saved to: ", raster)
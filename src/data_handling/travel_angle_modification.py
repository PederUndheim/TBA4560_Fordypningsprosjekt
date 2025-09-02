import rasterio
import numpy as np

travel_angle_path = "data/flow-py_outputs/tif/FP_travel_angle.tif"
slope_path = "data/tif/slope.tif"
output_path = "data/flow-py_outputs/tif/FP_travel_angle_modified.tif"

no_data_value = -9999
slope_threshold = 30

# Open slope and travel angle rasters and read as arrays
with rasterio.open(slope_path) as slope_src:
    slope = slope_src.read(1)
    slope_meta = slope_src.meta.copy()

with rasterio.open(travel_angle_path) as travel_src:
    travel = travel_src.read(1)
    travel_meta = travel_src.meta.copy()

travel_meta.update(dtype=rasterio.float32, 
                   nodata=no_data_value)

# Apply the condiiton
travel_modified = np.where(slope > slope_threshold, no_data_value, travel)

# Write new raster
with rasterio.open(output_path, 'w', **travel_meta) as dst:
    dst.write(travel_modified.astype(rasterio.float32), 1)

print("Raster saved: ", output_path)





 
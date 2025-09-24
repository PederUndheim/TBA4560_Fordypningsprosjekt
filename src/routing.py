import os
import sys
import subprocess
from typing import Tuple, Dict

# --- GRASS paths ---
GISBASE = "/Applications/GRASS-8.4.app/Contents/Resources"
GRASS_DB = os.path.expanduser("~/grassdata")
GRASS_LOCATION = "routing_algorithm"
GRASS_MAPSET = "PERMANENT"

os.environ['GISBASE'] = GISBASE
os.environ['PATH'] += os.pathsep + os.path.join(GISBASE, 'bin')
os.environ['PATH'] += os.pathsep + os.path.join(GISBASE, 'scripts')
sys.path.append(os.path.join(GISBASE, 'etc', 'python'))

import grass.script as gs
import grass.script.setup as gsetup

# Initialize a GRASS session once per run
def init_grass():
    gsetup.init(GRASS_DB, GRASS_LOCATION, GRASS_MAPSET)
    print(f"GRASS initialized: location={GRASS_LOCATION}, mapset={GRASS_MAPSET}")


# Import a single (x,y) point as a GRASS vector
def _import_points(name: str, coords: Tuple[float, float]):
    x, y = coords
    coords_str = f"{x},{y}\n"
    cmd = ["v.in.ascii", "input=-", f"output={name}", "separator=,", "--overwrite"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout_data, stderr_data = proc.communicate(input=coords_str)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to import points '{name}': {stderr_data}")
    if stdout_data:
        print(stdout_data.strip())
    print(f"Imported point {name} at ({x}, {y}).")


# Create a GRASS-safe layer name
def _safe_name(base: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in base)
    if out and out[0].isdigit():
        out = "_" + out
    return out



def run_routing_for_tour(
    tour_name: str,
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float],
    *,
    dem_path: str,
    cost_surface_path: str,
    lambda_weight: float,
    smooth_threshold: float,
    output_dir: str = "output"
) -> Dict[str, str]:
    """
    Run the full GRASS routing for a single tour and export outputs.
    Returns a dict with output file paths.
    """
    slug = _safe_name(tour_name.lower())
    dem_name = f"dem_{slug}"
    cost_name = f"cost_{slug}"
    start_vec = f"start_{slug}"
    end_vec = f"end_{slug}"

    cum_start = f"cum_start_{slug}"
    cum_end = f"cum_end_{slug}"
    direction_rast = f"dir_start_{slug}"
    corridor_rast = f"corridor_{slug}"
    drain_rast = f"drain_{slug}"
    optimal_path = f"path_{slug}"
    smooth_path = f"path_smooth_{slug}"

    # Ensure output dirs
    os.makedirs(output_dir, exist_ok=True)
    corridor_dir = os.path.join(output_dir, "corridor")
    geojson_native_dir = os.path.join(output_dir, "path_geojson", "native")
    geojson_wgs84_dir = os.path.join(output_dir, "path_geojson", "wgs84")
    shp_dir = os.path.join(output_dir, "path_shp")

    for d in (corridor_dir, geojson_native_dir, geojson_wgs84_dir, shp_dir):
        os.makedirs(d, exist_ok=True)

    corridor_tif = os.path.join(corridor_dir, f"{slug}_corridor.tif")
    path_geojson = os.path.join(geojson_native_dir, f"{slug}_path.geojson")
    path_shp = os.path.join(shp_dir, f"{slug}_path.shp")

    # 1) Import rasters (DEM + cost) and points
    print(f"[{tour_name}] Importing rasters...")
    gs.run_command("r.in.gdal", input=dem_path, output=dem_name, overwrite=True)
    gs.run_command("r.in.gdal", input=cost_surface_path, output=cost_name, overwrite=True)

    print(f"[{tour_name}] Importing start/end points...")
    _import_points(start_vec, start_coords)
    _import_points(end_vec, end_coords)

    # 2) Cumulative costs (both directions) and direction raster from start
    print(f"[{tour_name}] Running r.walk (start -> all)...")
    gs.run_command(
        "r.walk",
        elevation=dem_name,
        friction=cost_name,
        start_points=start_vec,
        output=cum_start,
        outdir=direction_rast,
        lambda_=lambda_weight,
        overwrite=True
    )

    print(f"[{tour_name}] Running r.walk (end -> all)...")
    gs.run_command(
        "r.walk",
        elevation=dem_name,
        friction=cost_name,
        start_points=end_vec,
        output=cum_end,
        lambda_=lambda_weight,
        overwrite=True
    )

    # 3) Corridor
    print(f"[{tour_name}] Computing corridor...")
    gs.mapcalc(f"{corridor_rast} = {cum_start} + {cum_end}", overwrite=True)

    # 4) Extract optimal path using r.drain, then smooth
    print(f"[{tour_name}] Extracting optimal path with r.drain...")
    end_x, end_y = end_coords
    end_coord_str = f"{end_x},{end_y}"
    gs.run_command(
        "r.drain",
        input=cum_start,
        direction=direction_rast,
        output=drain_rast,
        drain=optimal_path,          # vector output
        start_coordinates=end_coord_str,
        overwrite=True
    )

    print(f"[{tour_name}] Smoothing path with v.generalize (Douglas-Peucker)...")
    gs.run_command(
        "v.generalize",
        input=optimal_path,
        output=smooth_path,
        method="douglas",
        threshold=smooth_threshold,
        overwrite=True
    )

    # 5) Export: corridor GeoTIFF + path as Shapefile (native CRS) + GeoJSON (native CRS)
    print(f"[{tour_name}] Exporting corridor and vector path...")
    gs.run_command(
        "r.out.gdal",
        input=corridor_rast,
        output=corridor_tif,
        format="GTiff",
        overwrite=True
    )
    gs.run_command(
        "v.out.ogr",
        input=smooth_path,
        output=path_shp,
        format="ESRI_Shapefile",
        overwrite=True
    )
    gs.run_command(
        "v.out.ogr",
        input=smooth_path,
        output=path_geojson,
        format="GeoJSON",
        overwrite=True
    )

    return {
        "corridor_tif": corridor_tif,
        "path_shapefile": path_shp,
        "path_geojson_native": path_geojson  # Create a WGS84-GeoJSON in main.py
    }
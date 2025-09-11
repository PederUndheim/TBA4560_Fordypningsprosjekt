import os
import sys
import subprocess

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

# --- Initialize GRASS session ---
gsetup.init(GRASS_DB, GRASS_LOCATION, GRASS_MAPSET)
print(f"GRASS initialized: location={GRASS_LOCATION}, mapset={GRASS_MAPSET}")

# Input files
DEM_PATH = "data/tif/dem.tif"
COST_SURFACE_PATH = "output/cost_surface.tif"

OUTPUT_DIR = "output"
LAMBDA = 0.5 # weight between transit cost and movement cost

DEM_NAME = "dem"
COST_NAME = "cost_surface" 
POINTS_START = "points_start"
POINTS_END = "points_end"
CUM_COST_START = "cumulative_cost_start"
CUM_COST_END = "cumulative_cost_end"
CORRIDOR_RASTER = "corridor"
OPTIMAL_PATH = "optimal_path"
SMOOTH_PATH = "optimal_path_smooth"

def import_points(points_list, output_name):
    coords_str = "\n".join(f"{x},{y}" for x, y in points_list)
    cmd = ["v.in.ascii", "input=-", f"output={output_name}", "separator=,", "--overwrite"]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout_data, stderr_data = proc.communicate(input=coords_str)
    if proc.returncode != 0:
        raise Exception(f"Failed to import points '{output_name}': {stderr_data}")
    print(stdout_data)
    print(f"Successfully imported points for '{output_name}'.\n")


def import_rasters(start_coords, end_coords):
    print("Importing rasters and points into GRASS...")
    gs.run_command("r.in.gdal", input=DEM_PATH, output=DEM_NAME, overwrite=True)
    gs.run_command("r.in.gdal", input=COST_SURFACE_PATH, output=COST_NAME, overwrite=True)

    start_coords_str = f"x,y\n{start_coords[0]},{start_coords[1]}"
    end_coords_str = f"x,y\n{end_coords[0]},{end_coords[1]}"
    import_points([start_coords], POINTS_START)
    import_points([end_coords], POINTS_END)

# Run r.walk from points to compute cumulative cost
def compute_cumulative_cost(output_name, points_vector):
    print(f"Computing cumulative cost for {output_name} using {points_vector}...")
    gs.run_command("r.walk",
                   elevation=DEM_NAME,
                   friction=COST_NAME,
                   start_points=points_vector,
                   output=output_name,
                   lambda_=LAMBDA,
                   overwrite=True)
    print(f"Cumulative cost computed and saved as {output_name}.\n")
    return output_name

# Sum two cumulative cost rasters to create a corridor raster
def compute_corridor(cum_start, cum_end):
    print("Computing corridor raster...")
    gs.mapcalc(f"{CORRIDOR_RASTER} = {cum_start} + {cum_end}", overwrite=True)
    print(f"Corridor raster {CORRIDOR_RASTER} created.\n")
    return CORRIDOR_RASTER

# Extract optimal path with r.path and smooth it with v.generalize (Douglas-Peucker algorithm)
def extract_path(cumulative_raster):
    print("Generating direction raster from start points...")
    DIRECTION_RASTER = "direction_start"
    gs.run_command("r.walk",
               elevation=DEM_NAME,
               friction=COST_NAME,
               start_points=POINTS_START,
               output=CUM_COST_START,
               outdir=DIRECTION_RASTER,
               lambda_=LAMBDA,
               overwrite=True)
    
    print("Extracting optimal path...")
    end_coord_str = "136483,6962328"  # coordinates of the target
    gs.run_command("r.drain",
                input=CUM_COST_START,
                direction=DIRECTION_RASTER,
                output="drain_raster",  
                drain=OPTIMAL_PATH,  
                start_coordinates=end_coord_str,
                overwrite=True)

    
    print("Smoothing the optimal path...")
    gs.run_command("v.generalize",
                input=OPTIMAL_PATH,
                output=SMOOTH_PATH,
                method="douglas",
                threshold=10,
                overwrite=True)
    print(f"Optimal path saved as {SMOOTH_PATH}.\n")
    return SMOOTH_PATH

# Export corridor raster and path to output folder
def export_outputs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Exporting corridor raster and path shapefile...")
    gs.run_command("r.out.gdal",
                   input=CORRIDOR_RASTER,
                   output=os.path.join(OUTPUT_DIR, "corridor.tif"),
                   format="GTiff",
                   overwrite=True)
    gs.run_command("v.out.ogr", 
                   input=SMOOTH_PATH,
                   output=os.path.join(OUTPUT_DIR, "optimal_path.shp"),
                   format="ESRI_Shapefile",
                   overwrite=True)
    print("Export complete.\n")


def main():
    start_coords = (132504, 6959731)
    end_coords = (136483, 6962328)

    import_rasters(start_coords, end_coords)
    cum_start = compute_cumulative_cost(CUM_COST_START, POINTS_START)
    cum_end = compute_cumulative_cost(CUM_COST_END, POINTS_END)
    corridor_raster = compute_corridor(cum_start, cum_end)
    extract_path(corridor_raster)
    export_outputs()
    print("Routing workflow complete. Outputs saved in 'output/' folder.")


if __name__ == "__main__":
    main()

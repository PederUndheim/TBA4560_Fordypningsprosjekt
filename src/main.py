import os
import geopandas as gpd

from .cost_surface import config
from .cost_surface.cost_surface import create_cost_surface
from .routing import init_grass, run_routing_for_tour

SKITOURS = {
    "Kyrkjetaket": {
        "start": (132422.6, 6959926.2),
        "end":   (136483, 6962328),
    },
    "Galtatind": {
        "start": (132422.6, 6959926.2),
        "end":   (131960.2, 6962970.3),
    },
    "Loftskarstinden": {
        "start": (132422.6, 6959926.2),
        "end":   (132350.27, 6963820.49),
    },
    "Sore Klauva": {
        "start": (132422.6, 6959926.2),
        "end":   (135048.5, 6962996.58),
    },
    "Skarven": {
        "start": (132422.6, 6959926.2),
        "end":   (133710.6, 6962969.1),
    },
    "Kjovskarstinden": {
        "start": (132422.6, 6959926.2),
        "end":   (138549.8, 6962278.5),
    } 
}

def _safe_slug(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name.lower())
    if s and s[0].isdigit():
        s = "_" + s
    return s


# Load a native-CRS GeoJSON, reproject to EPSG:4326 (WGS84), save as .geojson
def export_wgs84_geojson(native_geojson_path: str, out_dir: str, out_basename: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{out_basename}.geojson")
    gdf = gpd.read_file(native_geojson_path)
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_wgs84.to_file(out_path, driver="GeoJSON")
    return out_path


def main():
    # 1) Build/refresh cost surface once
    print("=== Building cost surface ===")
    create_cost_surface(config.OUTPUT_COST, debug_mode=True)

    # 2) Init GRASS once
    print("\n=== Initializing GRASS ===")
    init_grass()

    # 3) Loop over tours and run routing
    print("\n=== Routing tours ===")
    final_outputs = {}

    for tour_name, pts in SKITOURS.items():
        print(f"\n--- Tour: {tour_name} ---")
        res = run_routing_for_tour(
            tour_name,
            start_coords=pts["start"],
            end_coords=pts["end"],
            dem_path=config.INPUT_RASTERS["dem"],
            cost_surface_path=config.OUTPUT_COST,
            lambda_weight=0.7,           # movement vs friction
            smooth_threshold=7.5,       # more/less generalization (1: little generalization, 100: VERY much generalization)
            output_dir="output"
        )

        # 4) Convert native-CRS GeoJSON to WGS84
        slug = _safe_slug(tour_name)
        tour_out_dir = os.path.join("output", slug)
        wgs84_geojson = export_wgs84_geojson(
            native_geojson_path=res["path_geojson_native"],
            out_dir=os.path.join("output", "path_geojson/wgs84"),
            out_basename=f"{slug}_path_wgs84"
        )

        # Collect paths for summary
        final_outputs[tour_name] = {
            "corridor_tif": res["corridor_tif"],
            "path_shapefile": res["path_shapefile"],
            "path_geojson_native": res["path_geojson_native"],
            "path_geojson_wgs84": wgs84_geojson,
        }

    # 5) Print a mini summary
    print("\n=== Done. Outputs ===")
    for tour_name, paths in final_outputs.items():
        print(f"\n[{tour_name}]")
        for k, v in paths.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
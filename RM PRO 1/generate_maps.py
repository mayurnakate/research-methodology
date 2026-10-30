"""
CLI Script to Generate All Standalone Dynamic Folium & Mapbox Maps
Author: Mayur Sanjay Nakate
Project: Visualizing Spatiotemporal Traffic Congestion Patterns using Dynamic Folium and Mapbox Layers
"""

import os
import json
import pandas as pd
from src.data_generator import generate_metropolitan_trajectories, get_network_gis_metadata, save_dataset
from src.congestion_analyzer import compute_congestion_indices, detect_spatiotemporal_bottlenecks
from src.export_utils import export_all_standalone_maps


def main():
    print("=" * 75)
    print(" SPATIOTEMPORAL TRAFFIC CONGESTION PATTERNS - MAP GENERATOR")
    print(" Author: Mayur Sanjay Nakate")
    print("=" * 75)
    
    data_csv = os.path.join("data", "bus_trajectories.csv")
    gis_json = os.path.join("data", "transit_network.json")
    
    if not os.path.exists(data_csv) or not os.path.exists(gis_json):
        print("[*] Generating fresh metropolitan transit trajectories and GIS network...")
        df = generate_metropolitan_trajectories()
        stations, routes_geo, bzones = get_network_gis_metadata()
        save_dataset(df, stations, routes_geo, bzones)
    else:
        print("[*] Loading existing trajectory dataset and GIS layers...")
        df = pd.read_csv(data_csv)
        with open(gis_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
            stations = meta["stations"]
            routes_geo = meta["routes"]
            
    print("[*] Analyzing congestion indices and running DBSCAN bottleneck clustering...")
    df = compute_congestion_indices(df)
    _, bottleneck_summary, _ = detect_spatiotemporal_bottlenecks(df)
    
    print("\n[*] Exporting interactive HTML maps & GIS GeoJSON layers...")
    generated_files = export_all_standalone_maps(df, stations, routes_geo, bottleneck_summary, output_dir="output")
    
    print("\n" + "=" * 75)
    print("[SUCCESS] All interactive visualizations generated successfully:")
    for gf in generated_files:
        print(f"  -> {gf}")
    print("=" * 75)
    print("You can double-click any .html file in 'output/' to open in your browser!")


if __name__ == "__main__":
    main()

"""
GIS and HTML Map Export Utilities
Author: Mayur Sanjay Nakate
Facilitates seamless export of Folium dynamic maps, Mapbox GL visualizations,
GeoJSON layers, and CSV performance summaries for GIS tools (QGIS, ArcGIS).
"""

import os
import json
import pandas as pd
from src.folium_layers import (
    create_base_map,
    add_transit_gis_infrastructure,
    add_bottleneck_clusters_layer,
    add_dynamic_heatmap_with_time,
    add_vehicle_trajectory_vectors,
    build_composite_folium_map
)
from src.mapbox_layers import build_mapbox_trajectory_deck, export_mapbox_html


def export_all_standalone_maps(df, stations, routes_geojson, bottleneck_summary_df, output_dir="output"):
    """Generate and save all standalone HTML maps and GIS files."""
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    # 1. Dynamic HeatMap With Time
    print("[*] Generating Folium Dynamic Heatmap HTML...")
    hm_map = create_base_map()
    add_transit_gis_infrastructure(hm_map, stations, routes_geojson)
    add_dynamic_heatmap_with_time(hm_map, df, auto_play=True)
    hm_path = os.path.join(output_dir, "dynamic_heatmap.html")
    hm_map.save(hm_path)
    generated_files.append(hm_path)
    print(f"[OK] Saved {hm_path}")
    
    # 2. Vehicle Trajectory Vectors & AntPath
    print("[*] Generating Vehicle Trajectory Vectors HTML...")
    traj_map = create_base_map()
    add_transit_gis_infrastructure(traj_map, stations, routes_geojson)
    add_vehicle_trajectory_vectors(traj_map, df, selected_hour=9, show_antpath=True)
    traj_path = os.path.join(output_dir, "trajectory_vectors.html")
    traj_map.save(traj_path)
    generated_files.append(traj_path)
    print(f"[OK] Saved {traj_path}")
    
    # 3. Bottleneck Zones GIS Map
    print("[*] Generating Bottleneck Clusters GIS Map HTML...")
    bn_map = create_base_map()
    add_transit_gis_infrastructure(bn_map, stations, routes_geojson)
    if not bottleneck_summary_df.empty:
        add_bottleneck_clusters_layer(bn_map, bottleneck_summary_df)
    bn_path = os.path.join(output_dir, "bottleneck_zones.html")
    bn_map.save(bn_path)
    generated_files.append(bn_path)
    print(f"[OK] Saved {bn_path}")
    
    # 4. Integrated Composite Master GIS Map
    print("[*] Generating Master Composite GIS Map HTML...")
    comp_map = build_composite_folium_map(df, stations, routes_geojson, bottleneck_summary_df, mode="all")
    comp_path = os.path.join(output_dir, "composite_gis_map.html")
    comp_map.save(comp_path)
    generated_files.append(comp_path)
    print(f"[OK] Saved {comp_path}")
    
    # 5. Mapbox GL / PyDeck 3D Visualization
    print("[*] Generating Mapbox GL 3D Hexagon & Trajectory Vectors HTML...")
    mapbox_path = os.path.join(output_dir, "mapbox_3d_trajectories.html")
    deck = build_mapbox_trajectory_deck(df, selected_hour=9)
    export_mapbox_html(deck, mapbox_path)
    generated_files.append(mapbox_path)
    
    # 6. Export Stations GeoJSON
    stations_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"station_name": s["station_name"], "route_id": s["route_id"]},
                "geometry": {"type": "Point", "coordinates": [s["longitude"], s["latitude"]]}
            }
            for s in stations
        ]
    }
    st_path = os.path.join(output_dir, "transit_stations.geojson")
    with open(st_path, "w", encoding="utf-8") as f:
        json.dump(stations_geojson, f, indent=2)
    generated_files.append(st_path)
    
    # 7. Export Routes GeoJSON
    rt_path = os.path.join(output_dir, "transit_corridors.geojson")
    with open(rt_path, "w", encoding="utf-8") as f:
        json.dump(routes_geojson, f, indent=2)
    generated_files.append(rt_path)
    
    return generated_files

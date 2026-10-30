"""
End-to-End Test and Benchmark Pipeline
Author: Mayur Sanjay Nakate
Project: Visualizing Spatiotemporal Traffic Congestion Patterns using Dynamic Folium and Mapbox Layers
"""

import os
import sys
import time
import json
import pandas as pd

from src.data_generator import generate_metropolitan_trajectories, get_network_gis_metadata, save_dataset
from src.congestion_analyzer import (
    compute_congestion_indices,
    detect_spatiotemporal_bottlenecks,
    get_hourly_route_analytics
)
from src.export_utils import export_all_standalone_maps


def run_pipeline():
    start_time = time.time()
    print("=" * 80)
    print(" METROPOLITAN BUS TRANSIT CONGESTION VISUALIZATION PIPELINE")
    print(" Author: Mayur Sanjay Nakate")
    print(" Technology: Python, Folium, Mapbox GL / PyDeck, Scikit-learn, DBSCAN")
    print("=" * 80)
    
    # Step 1: Trajectory Simulation
    print("\n[STEP 1/5] Simulating Metropolitan Transit Fleet & Trajectory Network...")
    df = generate_metropolitan_trajectories()
    stations, routes_geo, bzones = get_network_gis_metadata()
    save_dataset(df, stations, routes_geo, bzones, data_dir="data")
    print(f" -> Generated {len(df):,} GPS pings across {len(routes_geo['features'])} transit corridors.")
    
    # Step 2: Index Formulation & Performance Metrics
    print("\n[STEP 2/5] Formulating Traffic Congestion Performance Indices (SPI, TCI, Delay)...")
    df = compute_congestion_indices(df)
    mean_speed = df["speed_kmh"].mean()
    mean_spi = df["spi"].mean()
    severe_ratio = (df["congestion_code"] == 3).mean() * 100.0
    print(f" -> Network Average Speed: {mean_speed:.2f} km/h")
    print(f" -> Speed Performance Index (SPI): {mean_spi:.2f}%")
    print(f" -> Severe Congestion Frequency: {severe_ratio:.2f}% of samples")
    
    # Step 3: Spatiotemporal Bottleneck Clustering (DBSCAN)
    print("\n[STEP 3/5] Applying Spatiotemporal DBSCAN Density Clustering to Extract Bottlenecks...")
    congested_df, b_summary, b_geo = detect_spatiotemporal_bottlenecks(df)
    print(f" -> Congested samples isolated: {len(congested_df):,}")
    print(f" -> Persistent Bottleneck Clusters identified: {len(b_summary)}")
    for idx, row in b_summary.iterrows():
        print(f"    * [{row['bottleneck_id']}] {row['classification']} | Severity: {row['severity_score']:.1f} | Avg Speed: {row['avg_speed_kmh']:.1f} km/h | Peak: {row['peak_hour']:02d}:00")
        
    os.makedirs("output", exist_ok=True)
    b_summary.to_csv(os.path.join("output", "bottlenecks_detected.csv"), index=False)
    with open(os.path.join("output", "bottlenecks.geojson"), "w", encoding="utf-8") as f:
        json.dump(b_geo, f, indent=2)
        
    # Step 4: Standalone HTML Map Generation
    print("\n[STEP 4/5] Rendering Dynamic Folium and Mapbox GL Web Layers...")
    exported_files = export_all_standalone_maps(df, stations, routes_geo, b_summary, output_dir="output")
    print(f" -> Exported {len(exported_files)} standalone maps and GIS assets.")
    
    # Step 5: Hourly Analytics Verification
    print("\n[STEP 5/5] Generating Corridor-Level Spatiotemporal Matrices...")
    hourly = get_hourly_route_analytics(df)
    print(f" -> Aggregated {len(hourly)} hourly corridor performance bins.")
    
    total_duration = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"[PIPELINE COMPLETE] Executed successfully in {total_duration:.2f} seconds.")
    print("=" * 80)
    print("To launch the interactive dashboard, run:")
    print("  streamlit run app.py")
    print("To inspect exported maps, check the 'output/' directory.")


if __name__ == "__main__":
    run_pipeline()

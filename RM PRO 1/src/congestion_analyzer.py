"""
Spatiotemporal Traffic Congestion & Bottleneck Analysis Engine
Author: Mayur Sanjay Nakate
Calculates Speed Performance Index (SPI), Transit Congestion Index (TCI),
and employs DBSCAN clustering to detect recurrent metropolitan bottlenecks.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


def compute_congestion_indices(df, free_flow_col="free_flow_speed", speed_col="speed_kmh"):
    """
    Compute rigorous transportation engineering performance indices:
    - Speed Performance Index (SPI)
    - Transit Congestion Index (TCI)
    - Travel Rate Deficit (sec/km)
    """
    df = df.copy()
    
    # SPI: Speed Performance Index [0 - 100]
    df["spi"] = np.clip((df[speed_col] / df[free_flow_col]) * 100.0, 0.0, 100.0)
    
    # TCI: Transit Congestion Index [0 (free flow) to 1.0 (gridlock)]
    df["tci"] = np.clip(1.0 - (df[speed_col] / df[free_flow_col]), 0.0, 1.0)
    
    # Travel rate (seconds to travel 1 km)
    # 3600 / speed_kmh
    safe_speed = np.maximum(df[speed_col], 1.0)
    actual_rate = 3600.0 / safe_speed
    free_flow_rate = 3600.0 / df[free_flow_col]
    df["delay_rate_sec_per_km"] = np.maximum(0.0, actual_rate - free_flow_rate)
    
    return df


def detect_spatiotemporal_bottlenecks(
    df,
    spi_threshold=35.0,
    eps_meters=350.0,
    min_samples=25,
    earth_radius_m=6371000.0
):
    """
    Detect spatiotemporal bottlenecks using DBSCAN spatial density clustering
    on congested trajectory points (SPI <= threshold).
    
    Returns:
    - clustered_points_df: Original df with cluster labels (-1 = noise)
    - bottleneck_summary_df: Summary metrics per detected bottleneck cluster
    - bottleneck_geojson: GeoJSON feature collection for GIS mapping
    """
    # Filter points experiencing severe or heavy slowdown
    congested_df = df[df["spi"] <= spi_threshold].copy()
    
    if len(congested_df) < min_samples:
        print("[!] Insufficient congested trajectory points for clustering.")
        return congested_df, pd.DataFrame(), {"type": "FeatureCollection", "features": []}
        
    # Convert lat/lon coordinates to radians for haversine metric DBSCAN
    coords_rad = np.radians(congested_df[["latitude", "longitude"]].values)
    eps_rad = eps_meters / earth_radius_m
    
    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
    congested_df["cluster_id"] = db.fit_predict(coords_rad)
    
    # Analyze valid clusters (ignore noise labeled as -1)
    valid_clusters = congested_df[congested_df["cluster_id"] != -1]
    
    bottleneck_list = []
    geojson_features = []
    
    for cid, grp in valid_clusters.groupby("cluster_id"):
        centroid_lat = grp["latitude"].mean()
        centroid_lon = grp["longitude"].mean()
        
        # Calculate cluster radius (90th percentile distance from centroid)
        dists = np.sqrt(
            ((grp["latitude"] - centroid_lat) * 111000.0) ** 2 +
            ((grp["longitude"] - centroid_lon) * 111000.0 * np.cos(np.radians(centroid_lat))) ** 2
        )
        radius_m = float(np.percentile(dists, 90))
        
        avg_speed = grp["speed_kmh"].mean()
        min_speed = grp["speed_kmh"].min()
        avg_spi = grp["spi"].mean()
        avg_tci = grp["tci"].mean()
        avg_delay_rate = grp["delay_rate_sec_per_km"].mean()
        
        # Distinct vehicles & routes impacted
        impacted_vehicles = grp["vehicle_id"].nunique()
        impacted_routes = list(grp["route_id"].unique())
        
        # Temporal persistence
        active_hours = sorted(list(grp["hour"].unique()))
        hour_span = len(active_hours)
        peak_hour = grp["hour"].mode()[0]
        
        # Bottleneck Severity Score (BSS) formulation:
        # BSS = (1 - avg_spi/100) * ln(num_points + 1) * (duration_hours / 12) * 100
        severity_score = (1.0 - (avg_spi / 100.0)) * np.log1p(len(grp)) * (hour_span / 6.0) * 20.0
        
        # Classification
        if hour_span >= 4:
            classification = "Persistent Structural Chokepoint"
        elif hour_span >= 2:
            classification = "Recurrent Peak Hour Bottleneck"
        else:
            classification = "Transient / Incidental Congestion"
            
        b_info = {
            "bottleneck_id": f"BN-CLUSTER-{cid+1:02d}",
            "centroid_lat": round(centroid_lat, 6),
            "centroid_lon": round(centroid_lon, 6),
            "radius_meters": round(max(radius_m, 120.0), 1),
            "total_congested_points": int(len(grp)),
            "impacted_vehicles_count": int(impacted_vehicles),
            "impacted_routes": ", ".join(impacted_routes),
            "avg_speed_kmh": round(avg_speed, 2),
            "min_speed_kmh": round(min_speed, 2),
            "avg_spi": round(avg_spi, 2),
            "avg_tci": round(avg_tci, 3),
            "avg_delay_rate_sec_km": round(avg_delay_rate, 1),
            "peak_hour": int(peak_hour),
            "active_hours": ", ".join(map(str, active_hours)),
            "active_hours_count": int(hour_span),
            "severity_score": round(severity_score, 2),
            "classification": classification
        }
        bottleneck_list.append(b_info)
        
        # GeoJSON Point Feature
        geojson_features.append({
            "type": "Feature",
            "properties": b_info,
            "geometry": {
                "type": "Point",
                "coordinates": [round(centroid_lon, 6), round(centroid_lat, 6)]
            }
        })
        
    bottleneck_summary_df = pd.DataFrame(bottleneck_list)
    if not bottleneck_summary_df.empty:
        bottleneck_summary_df = bottleneck_summary_df.sort_values("severity_score", ascending=False).reset_index(drop=True)
        
    bottleneck_geojson = {
        "type": "FeatureCollection",
        "features": geojson_features
    }
    
    return congested_df, bottleneck_summary_df, bottleneck_geojson


def get_hourly_route_analytics(df):
    """Aggregate speed, delay, and congestion performance by route and hour."""
    hourly = df.groupby(["route_id", "route_name", "hour"]).agg(
        avg_speed=("speed_kmh", "mean"),
        min_speed=("speed_kmh", "min"),
        avg_spi=("spi", "mean"),
        avg_delay_sec=("schedule_delay_sec", "mean"),
        total_pings=("speed_kmh", "count"),
        severe_count=("congestion_code", lambda x: (x == 3).sum())
    ).reset_index()
    
    hourly["severe_pct"] = (hourly["severe_count"] / hourly["total_pings"]) * 100.0
    return hourly


def get_spatiotemporal_heatmap_matrix(df):
    """Create a pivot table of hour vs route average SPI for heatmaps."""
    matrix = df.pivot_table(index="route_name", columns="hour", values="spi", aggfunc="mean").round(1)
    return matrix


if __name__ == "__main__":
    data_path = os.path.join("data", "bus_trajectories.csv")
    if os.path.exists(data_path):
        raw_df = pd.read_csv(data_path)
        analyzed_df = compute_congestion_indices(raw_df)
        _, b_summary, b_geo = detect_spatiotemporal_bottlenecks(analyzed_df)
        print("[OK] Congestion index computation complete.")
        print(f"[OK] Detected {len(b_summary)} distinct spatiotemporal bottleneck zones:")
        print(b_summary[["bottleneck_id", "centroid_lat", "centroid_lon", "avg_speed_kmh", "severity_score", "classification"]])
        
        os.makedirs("output", exist_ok=True)
        b_summary.to_csv(os.path.join("output", "bottlenecks_detected.csv"), index=False)
        with open(os.path.join("output", "bottlenecks.geojson"), "w", encoding="utf-8") as f:
            json.dump(b_geo, f, indent=2)
        print("[OK] Exported bottleneck summary and GeoJSON.")
    else:
        print("[!] bus_trajectories.csv not found. Run data_generator.py first.")

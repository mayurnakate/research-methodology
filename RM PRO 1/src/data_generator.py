"""
Metropolitan Bus Transit Network & Trajectory Data Generator
Author: Mayur Sanjay Nakate
Generates high-fidelity spatiotemporal transit trajectories and GIS layers
reflecting realistic urban congestion bottlenecks, peak hours, and transit dynamics.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Reference Metropolitan Center (Pune-Mumbai Tech Corridor Metropolis)
BASE_LAT = 18.5204
BASE_LON = 73.8567

# Structural Bottleneck Hotspots in the Metropolitan Area
METRO_BOTTLENECK_ZONES = [
    {
        "zone_id": "BN-01",
        "name": "Central CBD Arterial Intersection",
        "lat": 18.5280,
        "lon": 73.8640,
        "radius_meters": 350,
        "peak_speed_reduction": 0.75, # 75% speed drop
        "peak_hours": [(8, 11), (17, 21)],
        "type": "Signalized Chokepoint & Intersection"
    },
    {
        "zone_id": "BN-02",
        "name": "Tech Corridor & Flyover Merge Point",
        "lat": 18.5590,
        "lon": 73.8070,
        "radius_meters": 450,
        "peak_speed_reduction": 0.82,
        "peak_hours": [(8, 12), (18, 22)],
        "type": "Highway Merge & Weaving Bottleneck"
    },
    {
        "zone_id": "BN-03",
        "name": "Railway Station & Multimodal Transit Terminal",
        "lat": 18.5295,
        "lon": 73.8745,
        "radius_meters": 400,
        "peak_speed_reduction": 0.70,
        "peak_hours": [(7, 10), (16, 20)],
        "type": "High Pedestrian & Multi-modal Spillover"
    },
    {
        "zone_id": "BN-04",
        "name": "University Circle & Radial Junction",
        "lat": 18.5410,
        "lon": 73.8290,
        "radius_meters": 380,
        "peak_speed_reduction": 0.65,
        "peak_hours": [(8, 11), (17, 19)],
        "type": "Rotary/Roundabout Capacity Deficiency"
    },
    {
        "zone_id": "BN-05",
        "name": "Industrial Park River Bridge Crossing",
        "lat": 18.4980,
        "lon": 73.8420,
        "radius_meters": 500,
        "peak_speed_reduction": 0.68,
        "peak_hours": [(7, 10), (17, 20)],
        "type": "Narrow Bridge Chokepoint"
    }
]

# Metropolitan Transit Corridors & Bus Routes
ROUTES_SPEC = [
    {
        "route_id": "R101",
        "name": "CBD Express (Central CBD - Tech Park)",
        "color": "#E63946",
        "waypoints": [
            (18.5150, 73.8480, "Swargate Central Terminal"),
            (18.5280, 73.8640, "CBD Arterial Hub"),
            (18.5360, 73.8450, "Civic Plaza"),
            (18.5410, 73.8290, "University Junction"),
            (18.5590, 73.8070, "Tech Park Phase 1"),
            (18.5720, 73.7850, "Silicon High-Tech Zone")
        ],
        "bus_count": 8,
        "free_flow_speed": 48.0
    },
    {
        "route_id": "R102",
        "name": "North-South Transit Spine (Rail Terminal - Airport)",
        "color": "#1D3557",
        "waypoints": [
            (18.4950, 73.8400, "South Suburb Depot"),
            (18.5150, 73.8480, "Swargate Central Terminal"),
            (18.5295, 73.8745, "Metropolitan Rail Junction"),
            (18.5450, 73.8900, "Koregaon East Hub"),
            (18.5680, 73.9100, "Airport Boulevard Station"),
            (18.5800, 73.9210, "International Airport Terminal")
        ],
        "bus_count": 7,
        "free_flow_speed": 45.0
    },
    {
        "route_id": "R103",
        "name": "Radial Ring Corridor (East-West Bypass)",
        "color": "#2A9D8F",
        "waypoints": [
            (18.5590, 73.8070, "Tech Park Phase 1"),
            (18.5410, 73.8290, "University Junction"),
            (18.5360, 73.8450, "Civic Plaza"),
            (18.5295, 73.8745, "Metropolitan Rail Junction"),
            (18.5180, 73.8980, "Hadapsar Industrial Arterial")
        ],
        "bus_count": 6,
        "free_flow_speed": 46.0
    },
    {
        "route_id": "R104",
        "name": "Downtown Circulator (City Center Loop)",
        "color": "#F4A261",
        "waypoints": [
            (18.5280, 73.8640, "CBD Arterial Hub"),
            (18.5295, 73.8745, "Metropolitan Rail Junction"),
            (18.5220, 73.8600, "Heritage Market Square"),
            (18.5150, 73.8480, "Swargate Central Terminal"),
            (18.5280, 73.8640, "CBD Arterial Hub")
        ],
        "bus_count": 5,
        "free_flow_speed": 35.0
    }
]


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c


def interpolate_route_waypoints(waypoints, density_meters=60):
    """Interpolate smooth dense GPS track points between waypoints."""
    detailed_points = []
    for i in range(len(waypoints) - 1):
        lat1, lon1, name1 = waypoints[i]
        lat2, lon2, name2 = waypoints[i + 1]
        dist = haversine_distance_meters(lat1, lon1, lat2, lon2)
        steps = max(int(dist / density_meters), 5)
        
        for s in range(steps):
            frac = s / steps
            interp_lat = lat1 + (lat2 - lat1) * frac
            interp_lon = lon1 + (lon2 - lon1) * frac
            # Add micro road curvature jitter to reflect real road geometry
            jitter_lat = np.sin(frac * np.pi) * 0.0003 * np.cos(i)
            jitter_lon = np.sin(frac * np.pi) * 0.0003 * np.sin(i)
            detailed_points.append({
                "lat": interp_lat + jitter_lat,
                "lon": interp_lon + jitter_lon,
                "segment_index": i,
                "station_from": name1,
                "station_to": name2
            })
    last_lat, last_lon, last_name = waypoints[-1]
    detailed_points.append({
        "lat": last_lat,
        "lon": last_lon,
        "segment_index": len(waypoints) - 2,
        "station_from": waypoints[-2][2],
        "station_to": last_name
    })
    return detailed_points


def get_bottleneck_factor(lat, lon, hour):
    """
    Check if a point falls within any bottleneck zone and calculate speed reduction factor
    based on distance to center and time of day.
    """
    max_reduction = 0.0
    active_bottleneck = None
    
    for bz in METRO_BOTTLENECK_ZONES:
        # Check temporal active window
        is_active_time = any(start <= hour < end for start, end in bz["peak_hours"])
        if not is_active_time:
            continue
            
        dist = haversine_distance_meters(lat, lon, bz["lat"], bz["lon"])
        if dist <= bz["radius_meters"]:
            # Intensity peaks at center, tapers toward radius perimeter
            spatial_factor = (1.0 - (dist / bz["radius_meters"])) ** 1.5
            reduction = bz["peak_speed_reduction"] * spatial_factor
            if reduction > max_reduction:
                max_reduction = reduction
                active_bottleneck = bz["name"]
                
    return max_reduction, active_bottleneck


def generate_metropolitan_trajectories(
    start_date="2026-10-28",
    hours_to_simulate=(7, 22),
    sample_interval_sec=30,
    random_seed=42
):
    """
    Generate realistic spatiotemporal GPS trajectory records for metropolitan bus transit.
    Simulates peak periods, vehicle queuing, signal delays, and free-flow night conditions.
    """
    np.random.seed(random_seed)
    records = []
    base_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Precompute route path geometries
    route_paths = {}
    for r in ROUTES_SPEC:
        route_paths[r["route_id"]] = interpolate_route_waypoints(r["waypoints"])

    print(f"[*] Simulating metropolitan bus transit trajectories between {hours_to_simulate[0]}:00 and {hours_to_simulate[1]}:00...")

    for r in ROUTES_SPEC:
        rid = r["route_id"]
        rname = r["name"]
        color = r["color"]
        ff_speed = r["free_flow_speed"]
        path = route_paths[rid]
        num_points = len(path)
        
        # Deploy buses staggered across the time window
        for b in range(r["bus_count"]):
            vid = f"BUS-{rid}-{b+1:02d}"
            # Stagger departures every 15-25 minutes
            start_offset_minutes = b * 22
            current_time = base_dt + timedelta(hours=hours_to_simulate[0], minutes=start_offset_minutes)
            end_time = base_dt + timedelta(hours=hours_to_simulate[1])
            
            direction = 1  # 1 = forward along waypoints, -1 = return trip
            curr_idx = 0
            
            while current_time < end_time:
                pt = path[curr_idx]
                hour = current_time.hour
                
                # Check bottleneck influence
                red_factor, bottleneck_name = get_bottleneck_factor(pt["lat"], pt["lon"], hour)
                
                # Base speed with general time-of-day traffic variation
                if (8 <= hour <= 10) or (17 <= hour <= 20):
                    time_penalty = np.random.uniform(0.20, 0.35)
                elif 12 <= hour <= 15:
                    time_penalty = np.random.uniform(0.05, 0.15)
                else:
                    time_penalty = 0.05
                    
                actual_reduction = min(0.88, red_factor + time_penalty)
                actual_speed = max(3.5, ff_speed * (1.0 - actual_reduction) + np.random.normal(0, 1.5))
                
                # Calculate speed performance index (SPI)
                spi = (actual_speed / ff_speed) * 100.0
                
                # Congestion category
                if spi <= 25.0:
                    congestion_state = "Severe Congestion"
                    congestion_code = 3
                elif spi <= 50.0:
                    congestion_state = "Moderate Delay"
                    congestion_code = 2
                elif spi <= 75.0:
                    congestion_state = "Mild Slowdown"
                    congestion_code = 1
                else:
                    congestion_state = "Free Flow"
                    congestion_code = 0
                    
                # Schedule deviation and passenger load simulation
                schedule_delay = max(0, int((1.0 - (spi / 100.0)) * 420 + np.random.normal(30, 10)))
                passenger_load = int(np.clip(
                    (35 if (8 <= hour <= 10 or 17 <= hour <= 20) else 18) + np.random.normal(0, 8),
                    5, 65
                ))
                
                records.append({
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "hour": hour,
                    "minute": current_time.minute,
                    "time_step": f"{hour:02d}:{current_time.minute // 15 * 15:02d}", # 15-min spatiotemporal bin
                    "vehicle_id": vid,
                    "route_id": rid,
                    "route_name": rname,
                    "route_color": color,
                    "latitude": round(pt["lat"], 6),
                    "longitude": round(pt["lon"], 6),
                    "speed_kmh": round(actual_speed, 2),
                    "free_flow_speed": ff_speed,
                    "spi": round(spi, 2),
                    "congestion_state": congestion_state,
                    "congestion_code": congestion_code,
                    "schedule_delay_sec": schedule_delay,
                    "passenger_load": passenger_load,
                    "station_from": pt["station_from"],
                    "station_to": pt["station_to"],
                    "bottleneck_source": bottleneck_name if bottleneck_name else "Normal Corridor"
                })
                
                # Advance bus along route based on actual speed
                # distance travelled in sample_interval_sec: (speed km/h * 1000 / 3600) * dt
                dist_moved = (actual_speed * 1000.0 / 3600.0) * sample_interval_sec
                step_increment = max(1, int(round(dist_moved / 60.0)))
                
                curr_idx += direction * step_increment
                
                # Handle route reversal at terminals
                if curr_idx >= num_points - 1:
                    curr_idx = num_points - 1
                    direction = -1
                    # Terminal dwell time
                    current_time += timedelta(minutes=5)
                elif curr_idx <= 0:
                    curr_idx = 0
                    direction = 1
                    # Terminal dwell time
                    current_time += timedelta(minutes=5)
                    
                current_time += timedelta(seconds=sample_interval_sec)

    df = pd.DataFrame(records)
    print(f"[OK] Generated {len(df):,} GPS spatiotemporal trajectory records across {len(ROUTES_SPEC)} transit routes.")
    return df


def get_network_gis_metadata():
    """Return GIS structural layers (routes GeoJSON and station markers)."""
    stations = []
    seen_stations = set()
    
    for r in ROUTES_SPEC:
        for lat, lon, name in r["waypoints"]:
            if name not in seen_stations:
                seen_stations.add(name)
                stations.append({
                    "station_name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "route_id": r["route_id"]
                })
                
    routes_geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for r in ROUTES_SPEC:
        coords = [[pt[1], pt[0]] for pt in r["waypoints"]]  # GeoJSON is [lon, lat]
        routes_geojson["features"].append({
            "type": "Feature",
            "properties": {
                "route_id": r["route_id"],
                "name": r["name"],
                "color": r["color"],
                "free_flow_speed": r["free_flow_speed"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        })
        
    return stations, routes_geojson, METRO_BOTTLENECK_ZONES


def save_dataset(df, stations, routes_geojson, bottlenecks, data_dir="data"):
    """Persist generated dataset and GIS metadata to files."""
    os.makedirs(data_dir, exist_ok=True)
    
    csv_path = os.path.join(data_dir, "bus_trajectories.csv")
    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved trajectory dataset to {csv_path}")
    
    gis_meta = {
        "stations": stations,
        "routes": routes_geojson,
        "bottlenecks": bottlenecks
    }
    gis_path = os.path.join(data_dir, "transit_network.json")
    with open(gis_path, "w", encoding="utf-8") as f:
        json.dump(gis_meta, f, indent=2)
    print(f"[OK] Saved transit network GIS metadata to {gis_path}")


if __name__ == "__main__":
    df = generate_metropolitan_trajectories()
    stations, routes_geo, bzones = get_network_gis_metadata()
    save_dataset(df, stations, routes_geo, bzones)

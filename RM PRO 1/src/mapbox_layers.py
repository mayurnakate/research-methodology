"""
Mapbox GL & PyDeck Spatiotemporal GIS Layer Engine
Author: Mayur Sanjay Nakate
Provides hardware-accelerated 3D vector trajectories, Mapbox GL styling,
HexagonLayer congestion elevation, and dynamic spatiotemporal layers.
"""

import pydeck as pdk
import pandas as pd
import numpy as np


def get_color_by_spi(spi):
    """Return RGBA color array based on Speed Performance Index (SPI)."""
    if spi <= 25:
        return [220, 20, 60, 220]    # Crimson Red (Heavy Congestion)
    elif spi <= 50:
        return [255, 140, 0, 200]   # Dark Orange (Moderate Delay)
    elif spi <= 75:
        return [255, 215, 0, 180]   # Gold / Yellow (Mild Slowdown)
    else:
        return [46, 204, 113, 160]  # Emerald Green (Free Flow)


def build_mapbox_trajectory_deck(
    df,
    selected_hour=None,
    selected_route=None,
    mapbox_style="mapbox://styles/mapbox/dark-v11",
    pitch=45,
    bearing=15
):
    """
    Build high-performance Mapbox GL / PyDeck spatiotemporal trajectory visualization
    with PathLayer vectors, 3D bottleneck columns, and interactive tooltips.
    """
    sub_df = df.copy()
    if selected_hour is not None:
        sub_df = sub_df[sub_df["hour"] == selected_hour]
    if selected_route is not None:
        sub_df = sub_df[sub_df["route_id"] == selected_route]
        
    # Prepare trajectory paths
    paths_data = []
    for vid, grp in sub_df.groupby("vehicle_id"):
        sorted_grp = grp.sort_values("timestamp")
        if len(sorted_grp) < 2:
            continue
            
        coords = sorted_grp[["longitude", "latitude"]].values.tolist()
        mean_spi = float(sorted_grp["spi"].mean())
        mean_speed = float(sorted_grp["speed_kmh"].mean())
        route_name = sorted_grp["route_name"].iloc[0]
        
        paths_data.append({
            "path": coords,
            "vehicle_id": vid,
            "route_name": route_name,
            "mean_spi": round(mean_spi, 1),
            "mean_speed": round(mean_speed, 1),
            "color": get_color_by_spi(mean_spi)
        })
        
    path_layer = pdk.Layer(
        "PathLayer",
        data=paths_data,
        pickable=True,
        width_scale=20,
        width_min_pixels=3,
        get_path="path",
        get_color="color",
        get_width=5
    )
    
    # 3D Hexagon Congestion Hotspots Layer
    congested_df = sub_df[sub_df["spi"] <= 40]
    hex_layer = pdk.Layer(
        "HexagonLayer",
        data=congested_df,
        get_position=["longitude", "latitude"],
        radius=180,
        elevation_scale=15,
        elevation_range=[0, 1000],
        pickable=True,
        extruded=True,
        coverage=0.88,
        color_range=[
            [255, 255, 178],
            [254, 204, 92],
            [253, 141, 60],
            [240, 59, 32],
            [189, 0, 38]
        ]
    )
    
    # Vehicle Position Nodes
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=sub_df,
        get_position=["longitude", "latitude"],
        get_color="[255 * (1 - spi/100), 220 * (spi/100), 50, 180]",
        get_radius=35,
        radius_min_pixels=3,
        radius_max_pixels=12,
        pickable=True
    )
    
    # View State centered at metropolitan network
    view_state = pdk.ViewState(
        latitude=float(sub_df["latitude"].mean()) if not sub_df.empty else 18.5350,
        longitude=float(sub_df["longitude"].mean()) if not sub_df.empty else 73.8500,
        zoom=12.2,
        pitch=pitch,
        bearing=bearing
    )
    
    tooltip = {
        "html": """
        <div style="background-color: #1e1e24; color: white; padding: 8px; border-radius: 4px; font-family: sans-serif; font-size: 12px;">
            <b>Vehicle:</b> {vehicle_id}<br/>
            <b>Route:</b> {route_name}<br/>
            <b>Speed:</b> {mean_speed} km/h (SPI: {mean_spi}%)<br/>
            <b>Congestion Density:</b> {elevationValue} pings
        </div>
        """,
        "style": {"color": "white"}
    }
    
    deck = pdk.Deck(
        layers=[path_layer, hex_layer, scatter_layer],
        initial_view_state=view_state,
        map_style=mapbox_style,
        tooltip=tooltip
    )
    
    return deck


def export_mapbox_html(deck, output_path="output/mapbox_trajectories.html"):
    """Export the PyDeck Mapbox GL map to standalone HTML."""
    deck.to_html(output_path, notebook_display=False)
    print(f"[OK] Exported Mapbox GL interactive map to {output_path}")

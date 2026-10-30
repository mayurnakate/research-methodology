"""
Dynamic Folium Spatiotemporal Visualization Engine
Author: Mayur Sanjay Nakate
Builds dynamic Folium HeatMapWithTime, animated AntPath vehicle trajectory vectors,
GIS transit corridors, station markers, and bottleneck zone overlays.
"""

import folium
from folium.plugins import HeatMapWithTime, AntPath, MiniMap, Fullscreen, FeatureGroupSubGroup


def create_base_map(center_lat=18.5350, center_lon=73.8500, zoom_start=12, tiles="OpenStreetMap"):
    """Initialize a GIS basemap with layer controls and full screen."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=tiles,
        control_scale=True
    )
    
    # Add alternative standard basemaps
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        name="CartoDB Positron",
        subdomains="abcd",
        max_zoom=19
    ).add_to(m)
    
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        name="CartoDB Dark Matter",
        subdomains="abcd",
        max_zoom=19
    ).add_to(m)
    
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    return m


def add_dynamic_heatmap_with_time(
    folium_map,
    df,
    time_col="hour",
    weight_col="tci",
    max_opacity=0.75,
    radius=18,
    auto_play=False
):
    """
    Construct dynamic Folium HeatMapWithTime layer across temporal time bins.
    Weight is derived from Transit Congestion Index (TCI = 1 - SPI/100).
    """
    time_steps = sorted(list(df[time_col].unique()))
    heat_data = []
    index_labels = []
    
    for t in time_steps:
        sub = df[df[time_col] == t]
        # Coordinates: [lat, lon, weight]
        step_points = sub[["latitude", "longitude", weight_col]].values.tolist()
        heat_data.append(step_points)
        index_labels.append(f"{t:02d}:00 Hrs")
        
    gradient_config = {
        0.2: "#00E5FF",  # Low congestion / Free flow cyan
        0.4: "#76FF03",  # Mild slowdown green
        0.6: "#FFD600",  # Moderate delay yellow
        0.8: "#FF6D00",  # Heavy delay orange
        1.0: "#D50000"   # Severe bottleneck crimson
    }
    
    hm = HeatMapWithTime(
        heat_data,
        index=index_labels,
        auto_play=auto_play,
        max_opacity=max_opacity,
        radius=radius,
        gradient=gradient_config,
        position="bottomleft",
        min_speed=1,
        max_speed=10,
        speed_step=1
    )
    hm.add_to(folium_map)
    return folium_map


def add_vehicle_trajectory_vectors(
    folium_map,
    df,
    selected_hour=None,
    selected_route=None,
    max_buses=12,
    show_antpath=True
):
    """
    Render vehicle trajectory vectors with directional arrows, AntPath animation,
    and speed-classified color segments.
    """
    sub_df = df.copy()
    if selected_hour is not None:
        sub_df = sub_df[sub_df["hour"] == selected_hour]
    if selected_route is not None:
        sub_df = sub_df[sub_df["route_id"] == selected_route]
        
    vector_group = folium.FeatureGroup(name="Bus Trajectory Vectors (Animated)")
    
    # Group by vehicle to plot individual paths
    vehicles = sub_df["vehicle_id"].unique()[:max_buses]
    
    for vid in vehicles:
        v_data = sub_df[sub_df["vehicle_id"] == vid].sort_values("timestamp")
        if len(v_data) < 2:
            continue
            
        coords = v_data[["latitude", "longitude"]].values.tolist()
        route_color = v_data["route_color"].iloc[0]
        route_name = v_data["route_name"].iloc[0]
        avg_v_speed = v_data["speed_kmh"].mean()
        avg_v_delay = v_data["schedule_delay_sec"].mean()
        
        # Add animated AntPath to signify vehicle flow
        if show_antpath:
            AntPath(
                locations=coords,
                color=route_color,
                pulse_color="#FFFFFF",
                delay=1000,
                weight=3.5,
                opacity=0.8,
                tooltip=f"<b>Vehicle:</b> {vid}<br><b>Route:</b> {route_name}<br><b>Avg Speed:</b> {avg_v_speed:.1f} km/h"
            ).add_to(vector_group)
            
        # Add head marker for active vehicle position
        latest_pt = v_data.iloc[-1]
        spi_val = latest_pt["spi"]
        status_color = "red" if spi_val <= 35 else ("orange" if spi_val <= 65 else "green")
        
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 220px;">
            <h4 style="margin: 0 0 5px 0; color: #1D3557;">Bus {vid}</h4>
            <b>Route:</b> {route_name}<br>
            <b>Instant Speed:</b> <span style="font-weight: bold; color: {status_color};">{latest_pt['speed_kmh']:.1f} km/h</span> (SPI: {spi_val:.1f}%)<br>
            <b>Congestion State:</b> {latest_pt['congestion_state']}<br>
            <b>Schedule Delay:</b> {latest_pt['schedule_delay_sec']} sec<br>
            <b>Passenger Load:</b> {latest_pt['passenger_load']} pax<br>
            <b>Segment:</b> {latest_pt['station_from']} &rarr; {latest_pt['station_to']}
        </div>
        """
        
        folium.CircleMarker(
            location=[latest_pt["latitude"], latest_pt["longitude"]],
            radius=6,
            color="#000000",
            weight=1.5,
            fill=True,
            fill_color=status_color,
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{vid} ({latest_pt['speed_kmh']:.1f} km/h)"
        ).add_to(vector_group)
        
    vector_group.add_to(folium_map)
    return folium_map


def add_transit_gis_infrastructure(folium_map, stations, routes_geojson):
    """Overlay transit network corridors and stop markers."""
    gis_group = folium.FeatureGroup(name="Transit Network Corridors & Stops")
    
    # Route Corridors
    for feature in routes_geojson.get("features", []):
        props = feature["properties"]
        geom = feature["geometry"]
        # GeoJSON is lon, lat -> Folium needs lat, lon
        folium_coords = [[pt[1], pt[0]] for pt in geom["coordinates"]]
        
        folium.PolyLine(
            locations=folium_coords,
            color=props.get("color", "#3388ff"),
            weight=4,
            opacity=0.7,
            dash_array="6, 6",
            tooltip=f"<b>Transit Route:</b> {props.get('name')}<br><b>Design Speed:</b> {props.get('free_flow_speed')} km/h"
        ).add_to(gis_group)
        
    # Stations
    for st in stations:
        folium.CircleMarker(
            location=[st["latitude"], st["longitude"]],
            radius=5,
            color="#1D3557",
            weight=2,
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=1.0,
            tooltip=f"Transit Stop: {st['station_name']}"
        ).add_to(gis_group)
        
    gis_group.add_to(folium_map)
    return folium_map


def add_bottleneck_clusters_layer(folium_map, bottleneck_summary_df):
    """Overlay detected spatiotemporal bottleneck zones with impact circles."""
    bn_group = folium.FeatureGroup(name="Identified Congestion Bottlenecks (DBSCAN)")
    
    for _, row in bottleneck_summary_df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 250px;">
            <h4 style="margin: 0 0 5px 0; color: #D50000;">{row['bottleneck_id']}</h4>
            <b>Classification:</b> {row['classification']}<br>
            <b>Severity Score:</b> <b>{row['severity_score']:.1f}</b><br>
            <b>Avg Bottleneck Speed:</b> {row['avg_speed_kmh']:.1f} km/h<br>
            <b>Speed Performance Index:</b> {row['avg_spi']:.1f}%<br>
            <b>Delay Rate Deficit:</b> +{row['avg_delay_rate_sec_km']:.0f} sec/km<br>
            <b>Peak Active Hours:</b> {row['active_hours']}<br>
            <b>Impacted Transit Lines:</b> {row['impacted_routes']}<br>
            <b>Impact Radius:</b> {row['radius_meters']} m
        </div>
        """
        
        # Outer impact circle
        folium.Circle(
            location=[row["centroid_lat"], row["centroid_lon"]],
            radius=row["radius_meters"],
            color="#D50000",
            weight=2,
            fill=True,
            fill_color="#D50000",
            fill_opacity=0.25,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"Bottleneck: {row['bottleneck_id']} (Severity: {row['severity_score']:.1f})"
        ).add_to(bn_group)
        
        # Inner epicenter icon
        folium.Marker(
            location=[row["centroid_lat"], row["centroid_lon"]],
            icon=folium.Icon(color="red", icon="warning", prefix="fa"),
            tooltip=f"{row['bottleneck_id']}: {row['classification']}"
        ).add_to(bn_group)
        
    bn_group.add_to(folium_map)
    return folium_map


def build_composite_folium_map(
    df,
    stations,
    routes_geojson,
    bottleneck_summary_df,
    mode="all",
    selected_hour=None,
    selected_route=None
):
    """Construct complete integrated Folium map with all layer controls."""
    m = create_base_map()
    
    # 1. Base GIS Infrastructure
    add_transit_gis_infrastructure(m, stations, routes_geojson)
    
    # 2. Identified Bottleneck Zones
    if not bottleneck_summary_df.empty:
        add_bottleneck_clusters_layer(m, bottleneck_summary_df)
        
    # 3. Dynamic Heatmap with Time OR Trajectory Vectors based on mode
    if mode in ["all", "heatmap"]:
        add_dynamic_heatmap_with_time(m, df, time_col="hour", weight_col="tci")
        
    if mode in ["all", "trajectories"]:
        add_vehicle_trajectory_vectors(
            m, df,
            selected_hour=selected_hour,
            selected_route=selected_route,
            show_antpath=True
        )
        
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    return m

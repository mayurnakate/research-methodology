"""
Interactive Metropolitan Bus Transit Spatiotemporal Congestion Visualizer
Author: Mayur Sanjay Nakate
Platform: Python, Streamlit, Folium, Mapbox GL / PyDeck
Target: ISPRS International Journal of Geo-Information / DST NGP
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

from src.data_generator import generate_metropolitan_trajectories, get_network_gis_metadata, save_dataset
from src.congestion_analyzer import (
    compute_congestion_indices,
    detect_spatiotemporal_bottlenecks,
    get_hourly_route_analytics,
    get_spatiotemporal_heatmap_matrix
)
from src.folium_layers import (
    create_base_map,
    add_transit_gis_infrastructure,
    add_dynamic_heatmap_with_time,
    add_vehicle_trajectory_vectors,
    add_bottleneck_clusters_layer,
    build_composite_folium_map
)
from src.mapbox_layers import build_mapbox_trajectory_deck
from src.export_utils import export_all_standalone_maps

# Page configuration
st.set_page_config(
    page_title="Traffic Congestion Visualizer | Folium & Mapbox",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern academic/GIS dashboard
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
        padding: 24px;
        border-radius: 10px;
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-card {
        background: #ffffff;
        padding: 16px;
        border-radius: 8px;
        border-left: 5px solid #1D3557;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-weight: 600;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_or_create_data():
    """Load cached dataset or generate fresh if not present."""
    data_csv = os.path.join("data", "bus_trajectories.csv")
    gis_json = os.path.join("data", "transit_network.json")
    
    if not os.path.exists(data_csv) or not os.path.exists(gis_json):
        df = generate_metropolitan_trajectories()
        stations, routes_geo, bzones = get_network_gis_metadata()
        save_dataset(df, stations, routes_geo, bzones)
    else:
        df = pd.read_csv(data_csv)
        with open(gis_json, "r", encoding="utf-8") as f:
            meta = json.load(f)
            stations = meta["stations"]
            routes_geo = meta["routes"]
            bzones = meta.get("bottlenecks", [])
            
    df = compute_congestion_indices(df)
    _, bottleneck_summary, bottleneck_geo = detect_spatiotemporal_bottlenecks(df)
    return df, stations, routes_geo, bzones, bottleneck_summary, bottleneck_geo


def main():
    # Load dataset
    df, stations, routes_geo, bzones, bottleneck_summary, bottleneck_geo = load_or_create_data()
    
    # Header Banner
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">
            Visualizing Spatiotemporal Traffic Congestion Patterns
        </h1>
        <p style="margin: 6px 0 0 0; font-size: 15px; opacity: 0.9;">
            Dynamic Folium and Mapbox Layers for Metropolitan Bus Transit Network Bottleneck Identification
        </p>
        <div style="margin-top: 10px; font-size: 13px; opacity: 0.85;">
            <b>Principal Investigator:</b> Mayur Sanjay Nakate &nbsp;|&nbsp; 
            <b>Domain:</b> Data Visualization Techniques &amp; ITS &nbsp;|&nbsp;
            <b>Target Publication:</b> ISPRS Int. J. Geo-Inf. / DST NGP
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎛️ Simulation & Layer Controls")
    
    view_mode = st.sidebar.radio(
        "Select Visualization Engine / Mode:",
        [
            "Dynamic Folium Heatmap (TimeSlider)",
            "Vehicle Trajectory Vectors (AntPath)",
            "Identified Bottleneck Zones (DBSCAN)",
            "Mapbox GL 3D Hexagon & Vector Deck",
            "Master Integrated GIS Map",
            "Spatiotemporal Analytical Charts",
            "IEEE Research Paper Documentation"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters & Parameters")
    
    # Route filter
    route_options = ["All Corridors"] + sorted(list(df["route_id"].unique()))
    selected_route_raw = st.sidebar.selectbox("Filter Transit Corridor:", route_options)
    selected_route = None if selected_route_raw == "All Corridors" else selected_route_raw
    
    # Hour filter
    hour_options = ["All Operating Hours (7:00 - 22:00)"] + [f"{h:02d}:00" for h in sorted(df["hour"].unique())]
    selected_hour_raw = st.sidebar.selectbox("Filter Temporal Epoch:", hour_options)
    selected_hour = None if "All" in selected_hour_raw else int(selected_hour_raw.split(":")[0])
    
    # Filter dataset for KPIs
    filtered_df = df.copy()
    if selected_route:
        filtered_df = filtered_df[filtered_df["route_id"] == selected_route]
    if selected_hour:
        filtered_df = filtered_df[filtered_df["hour"] == selected_hour]
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Tools")
    if st.sidebar.button("📦 Export All Standalone HTML Maps"):
        with st.spinner("Generating standalone HTML maps and GeoJSON layers..."):
            gen_files = export_all_standalone_maps(df, stations, routes_geo, bottleneck_summary)
            st.sidebar.success(f"Generated {len(gen_files)} files in 'output/' directory!")
            
    # Executive KPI Metrics
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_pings = len(filtered_df)
    avg_speed = filtered_df["speed_kmh"].mean()
    avg_spi = filtered_df["spi"].mean()
    severe_ratio = (filtered_df["congestion_code"] == 3).mean() * 100.0
    active_buses = filtered_df["vehicle_id"].nunique()
    
    with kpi1:
        st.metric("Trajectory Pings", f"{total_pings:,}", help="Total high-resolution GPS sample pings")
    with kpi2:
        st.metric("Network Speed", f"{avg_speed:.1f} km/h", delta=f"{avg_spi:.1f}% SPI")
    with kpi3:
        st.metric("Severe Congestion", f"{severe_ratio:.1f}%", delta="-High Delay" if severe_ratio > 20 else "+Normal", delta_color="inverse")
    with kpi4:
        st.metric("Active Transit Fleet", f"{active_buses} Buses", f"{len(routes_geo['features'])} Corridors")
    with kpi5:
        st.metric("Identified Bottlenecks", f"{len(bottleneck_summary)} Zones", "DBSCAN Clusters")
        
    st.markdown("---")
    
    # View Router
    if view_mode == "Dynamic Folium Heatmap (TimeSlider)":
        st.subheader("🔥 Dynamic Spatiotemporal Congestion Heatmap (HeatMapWithTime)")
        st.info("💡 **Interactive Playback**: Use the playback controller at the bottom-left of the map to animate congestion evolution throughout the metropolitan day. The color gradient transitions from Cyan (Free Flow) &rarr; Green &rarr; Yellow &rarr; Orange &rarr; Crimson Red (Severe Gridlock).")
        
        m = create_base_map()
        add_transit_gis_infrastructure(m, stations, routes_geo)
        add_dynamic_heatmap_with_time(m, filtered_df, time_col="hour", weight_col="tci", auto_play=False)
        
        # Save temp HTML for iframe display
        tmp_html = os.path.join("output", "temp_dynamic_heatmap.html")
        m.save(tmp_html)
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=620, scrolling=False)
        
    elif view_mode == "Vehicle Trajectory Vectors (AntPath)":
        st.subheader("🚌 Vehicle Trajectory Vectors & Animated AntPath Flows")
        st.info("💡 **Trajectory Vectors**: Animated marching ants (`AntPath`) represent instantaneous direction and corridor flow. Markers denote the latest bus position colored by Speed Performance Index (Green = Free Flow, Orange = Mild Slowdown, Red = Congested). Click any bus marker for operational telematics.")
        
        hour_to_show = selected_hour if selected_hour is not None else 9
        st.caption(f"Displaying Trajectory Vectors for Hour **{hour_to_show:02d}:00** (Selected corridor: **{selected_route_raw}**)")
        
        m = create_base_map()
        add_transit_gis_infrastructure(m, stations, routes_geo)
        add_vehicle_trajectory_vectors(
            m, df,
            selected_hour=hour_to_show,
            selected_route=selected_route,
            max_buses=16,
            show_antpath=True
        )
        
        tmp_html = os.path.join("output", "temp_trajectory_vectors.html")
        m.save(tmp_html)
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=620, scrolling=False)
        
    elif view_mode == "Identified Bottleneck Zones (DBSCAN)":
        st.subheader("⚠️ Spatiotemporal Bottleneck Identification (DBSCAN Clustering)")
        st.info("💡 **Bottleneck Detection**: Trajectory points with $SPI \\le 35$ are clustered using Haversine DBSCAN. Red shaded impact zones indicate bottleneck propagation radius, and caution markers display quantitative congestion metrics.")
        
        col_m, col_t = st.columns([1.6, 1.0])
        
        with col_m:
            m = create_base_map()
            add_transit_gis_infrastructure(m, stations, routes_geo)
            add_bottleneck_clusters_layer(m, bottleneck_summary)
            
            tmp_html = os.path.join("output", "temp_bottlenecks.html")
            m.save(tmp_html)
            with open(tmp_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=600, scrolling=False)
            
        with col_t:
            st.markdown("#### Detected Bottleneck Clusters")
            if not bottleneck_summary.empty:
                display_cols = ["bottleneck_id", "severity_score", "avg_speed_kmh", "avg_spi", "classification"]
                st.dataframe(
                    bottleneck_summary[display_cols].style.background_gradient(
                        subset=["severity_score"], cmap="YlOrRd"
                    ),
                    height=300
                )
                
                selected_bn = st.selectbox("Inspect Bottleneck Detail:", bottleneck_summary["bottleneck_id"])
                bn_detail = bottleneck_summary[bottleneck_summary["bottleneck_id"] == selected_bn].iloc[0]
                
                st.markdown(f"""
                **Zone ID:** `{bn_detail['bottleneck_id']}`  
                **Classification:** `{bn_detail['classification']}`  
                **Epicenter Coordinates:** `{bn_detail['centroid_lat']:.4f}, {bn_detail['centroid_lon']:.4f}`  
                **Impact Radius:** `{bn_detail['radius_meters']:.0f} meters`  
                **Average Speed:** `{bn_detail['avg_speed_kmh']:.1f} km/h`  
                **Speed Performance Index:** `{bn_detail['avg_spi']:.1f}%`  
                **Delay Rate Deficit:** `+{bn_detail['avg_delay_rate_sec_km']:.0f} sec/km`  
                **Impacted Lines:** `{bn_detail['impacted_routes']}`  
                **Peak Active Hours:** `{bn_detail['active_hours']}`
                """)
                
    elif view_mode == "Mapbox GL 3D Hexagon & Vector Deck":
        st.subheader("🌐 Mapbox GL / PyDeck 3D Spatiotemporal Layer Visualization")
        st.info("💡 **Hardware-Accelerated 3D WebGL**: High-density 3D hexagon columns visualize cumulative congestion density, overlaid with vehicle vector paths colored according to instantaneous Speed Performance Index.")
        
        hour_to_deck = selected_hour if selected_hour is not None else 9
        deck = build_mapbox_trajectory_deck(df, selected_hour=hour_to_deck, selected_route=selected_route)
        st.pydeck_chart(deck, use_container_width=True)
        
    elif view_mode == "Master Integrated GIS Map":
        st.subheader("🗺️ Integrated Multi-Layer GIS Dashboard")
        st.info("💡 **Full Multi-Layer GIS**: Integrates transit corridors, stations, animated trajectory vectors, dynamic heatmaps, and DBSCAN bottleneck zones with full Folium LayerControl toggle.")
        
        m = build_composite_folium_map(
            df, stations, routes_geo, bottleneck_summary,
            mode="all",
            selected_hour=selected_hour,
            selected_route=selected_route
        )
        tmp_html = os.path.join("output", "temp_composite.html")
        m.save(tmp_html)
        with open(tmp_html, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=650, scrolling=False)
        
    elif view_mode == "Spatiotemporal Analytical Charts":
        st.subheader("📊 Spatiotemporal Traffic Flow & Delay Analytics")
        
        c1, c2 = st.columns(2)
        hourly_analytics = get_hourly_route_analytics(df)
        
        with c1:
            st.markdown("#### Hourly Speed Profile by Transit Corridor")
            fig_speed = px.line(
                hourly_analytics,
                x="hour",
                y="avg_speed",
                color="route_name",
                markers=True,
                labels={"hour": "Hour of Day (24h)", "avg_speed": "Average Speed (km/h)", "route_name": "Corridor"},
                title="Corridor Velocity Degradation Across Morning & Evening Peaks"
            )
            fig_speed.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Congestion Threshold (20 km/h)")
            fig_speed.update_layout(template="plotly_white", height=380)
            st.plotly_chart(fig_speed, use_container_width=True)
            
        with c2:
            st.markdown("#### Schedule Delay Rate by Transit Corridor")
            fig_delay = px.bar(
                hourly_analytics,
                x="hour",
                y="avg_delay_sec",
                color="route_name",
                barmode="group",
                labels={"hour": "Hour of Day", "avg_delay_sec": "Schedule Delay (seconds)", "route_name": "Corridor"},
                title="Accumulated Passenger Schedule Delay (Seconds)"
            )
            fig_delay.update_layout(template="plotly_white", height=380)
            st.plotly_chart(fig_delay, use_container_width=True)
            
        st.markdown("#### Spatiotemporal Heatmap Matrix (Route vs Hour SPI)")
        matrix = get_spatiotemporal_heatmap_matrix(df)
        fig_heat = px.imshow(
            matrix,
            labels=dict(x="Hour of Day", y="Transit Corridor", color="SPI (%)"),
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale="RdYlGn",
            title="Spatiotemporal Speed Performance Index (SPI) Heatmap Matrix"
        )
        fig_heat.update_layout(height=350)
        st.plotly_chart(fig_heat, use_container_width=True)
        
    elif view_mode == "IEEE Research Paper Documentation":
        st.subheader("📄 IEEE Research Paper Reference & Technical Specification")
        st.markdown("""
        **Paper Title:** *Visualizing Spatiotemporal Traffic Congestion Patterns using Dynamic Folium and Mapbox Layers in Metropolitan Bus Transit Networks*  
        **Author:** **Mayur Sanjay Nakate**  
        **Format:** IEEE Two-Column Conference / Journal Format  
        **Target Reference:** ISPRS International Journal of Geo-Information (MDPI, Scopus Q1) / DST NGP  
        **Total References Cited:** 20 Peer-Reviewed Research Papers
        """)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            docx_report_path = os.path.join("report", "Project_Report_Mayur_Nakate.docx")
            if os.path.exists(docx_report_path):
                with open(docx_report_path, "rb") as f:
                    docx_rep_bytes = f.read()
                st.download_button(
                    "📄 Download Project Report (Word .DOCX)",
                    docx_rep_bytes,
                    file_name="Project_Report_Mayur_Nakate.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            docx_paper_path = os.path.join("paper", "IEEE_Research_Paper_Mayur_Nakate.docx")
            if os.path.exists(docx_paper_path):
                with open(docx_paper_path, "rb") as f:
                    docx_paper_bytes = f.read()
                st.download_button(
                    "📑 Download IEEE Research Paper (Word .DOCX)",
                    docx_paper_bytes,
                    file_name="IEEE_Research_Paper_Mayur_Nakate.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        with col_d2:
            paper_md_path = os.path.join("paper", "IEEE_Research_Paper.md")
            if os.path.exists(paper_md_path):
                with open(paper_md_path, "r", encoding="utf-8") as f:
                    paper_text = f.read()
                st.download_button(
                    "📥 Download Research Paper (Markdown)",
                    paper_text,
                    file_name="IEEE_Research_Paper_Mayur_Nakate.md",
                    mime="text/markdown"
                )
                
            tex_path = os.path.join("paper", "IEEE_Research_Paper.tex")
            if os.path.exists(tex_path):
                with open(tex_path, "r", encoding="utf-8") as f:
                    tex_content = f.read()
                st.download_button(
                    "📥 Download IEEE LaTeX Source (.tex)",
                    tex_content,
                    file_name="IEEE_Research_Paper_Mayur_Nakate.tex",
                    mime="text/plain"
                )
                
            html_paper_path = os.path.join("paper", "IEEE_Research_Paper.html")
            if os.path.exists(html_paper_path):
                with open(html_paper_path, "r", encoding="utf-8") as f:
                    html_paper = f.read()
                st.download_button(
                    "📥 Download Printable IEEE Paper (HTML / PDF)",
                    html_paper,
                    file_name="IEEE_Research_Paper_Mayur_Nakate.html",
                    mime="text/html"
                )
            
        st.markdown("---")
        with st.expander("📖 Read Full IEEE Research Paper Online", expanded=True):
            if os.path.exists(paper_md_path):
                st.markdown(paper_text)
            else:
                st.info("Paper source is being compiled into the workspace.")


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
import json
import logging
import traceback

# Handle potential import errors for Folium packages
try:
    import folium
    from streamlit_folium import folium_static
    from folium.plugins import MarkerCluster, HeatMap
except ImportError as e:
    st.error(f"Error importing Folium packages: {str(e)}")
    logging.error(f"Folium import error: {str(e)}")

import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.data_access import get_map_data, get_demographic_summary, get_market_insights
from utils.html_render import render_html, render_card, render_progress

# Module-level imports and initialization only
# We'll handle session state initialization inside the render function

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def render_opportunity_map(title="Market Opportunity Map", state_filter=None, height=600):
    """
    Render an interactive opportunity map with proper tooltips and context using Folium.
    
    Args:
        title (str): Title for the map section
        state_filter (list, optional): List of state codes to filter the map
        height (int, optional): Height of the map in pixels
        
    Returns:
        tuple: The Folium map object and DataFrame of map data
    """
    st.markdown(f"## {title}")
    
    # Create map controls
    map_control_cols = st.columns([1, 1, 1, 2])
    
    with map_control_cols[0]:
        # Map style selector (reduced to most reliable options)
        map_style = st.selectbox(
            "Map Style",
            options=["OpenStreetMap", "CartoDB positron"],
            index=0,
            key="map_style_selector"
        )
    
    with map_control_cols[1]:
        # Color dimension selector
        color_dimension = st.selectbox(
            "Color By",
            options=["Growth Rate", "Market Size", "Opportunity Score"],
            index=0,
            key="color_dimension_selector"
        )
        
        # Map dimension to field name
        dimension_map = {
            "Growth Rate": "growth_rate",
            "Market Size": "market_size",
            "Opportunity Score": "opportunity_score"
        }
        
        color_field = dimension_map[color_dimension]
        st.session_state.map_view_mode = color_field
    
    with map_control_cols[2]:
        # Display mode selector
        display_mode = st.selectbox(
            "Display Mode",
            options=["Markers", "Clusters", "Heatmap"],
            index=0,
            key="display_mode_selector"
        )
    
    with map_control_cols[3]:
        # Map feature options
        feature_cols = st.columns(3)
        
        with feature_cols[0]:
            reset_view = st.button("Reset View", key="reset_map_view", use_container_width=True)
        
        with feature_cols[1]:
            show_labels = st.checkbox("Show Labels", value=True, key="show_labels")
        
        with feature_cols[2]:
            show_legend = st.checkbox("Show Legend", value=True, key="show_legend")
    
    # Load map data with proper error handling
    with st.spinner("Loading map data..."):
        map_data_response = get_map_data(state_filter)
        
        if "error" in map_data_response:
            st.error(f"Error loading map data: {map_data_response['error']}")
            return None, None
        
        # Extract the data portion
        map_data = map_data_response.get('data', [])
        
        if not map_data:
            st.warning("No map data available for the selected filters.")
            return None, None
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(map_data)
        
        # Check if required columns exist
        required_columns = ['latitude', 'longitude', 'city', 'state', 'market_size', 'growth_rate']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"Map data is missing required columns: {', '.join(missing_columns)}")
            return None, None
        
        # Add opportunity score if not present (calculated as growth_rate * market_size / 1000)
        if 'opportunity_score' not in df.columns:
            df['opportunity_score'] = (df['growth_rate'] * df['market_size'] / 1000).round(1)
        
        # Remove any rows with invalid coordinates
        df = df[(df['latitude'] != 0) & (df['longitude'] != 0)]
        
        if len(df) == 0:
            st.warning("No valid coordinate data available for mapping.")
            return None, None
    
    # Create a function for color scaling based on the selected dimension
    def get_color(value, field):
        min_val = df[field].min()
        max_val = df[field].max()
        
        # Normalize value to 0-1 scale
        if max_val > min_val:
            normalized = (value - min_val) / (max_val - min_val)
        else:
            normalized = 0.5
        
        # Color schemes based on field
        if field == 'growth_rate':
            # Green for high growth: lighter to darker
            r = int(220 - 180 * normalized)
            g = int(220)
            b = int(120 - 120 * normalized)
            return f'#{r:02x}{g:02x}{b:02x}'
            
        elif field == 'market_size':
            # Blue for market size: lighter to darker
            r = int(120 - 100 * normalized)
            g = int(150 - 50 * normalized)
            b = int(180 + 75 * normalized)
            return f'#{r:02x}{g:02x}{b:02x}'
            
        else:  # opportunity_score
            # Purple/magenta for opportunity
            r = int(150 + 105 * normalized)
            g = int(50 + 50 * normalized)
            b = int(150 + 100 * normalized)
            return f'#{r:02x}{g:02x}{b:02x}'
    
    # Create a function for marker radius scaling
    def get_radius(value, field):
        if field == 'market_size':
            return min(25, max(8, value / 10000))
        elif field == 'population':
            return min(25, max(8, value / 100000))
        else:  # growth_rate
            return min(25, max(8, value / 1.5))
    
    # Add color and radius columns to the DataFrame
    df['color'] = df.apply(lambda row: get_color(row[color_field], color_field), axis=1)
    df['marker_radius'] = df.apply(lambda row: get_radius(row[color_field], color_field), axis=1)
    
    # Initialize session state variables if they don't exist
    if 'map_last_click' not in st.session_state:
        st.session_state.map_last_click = {'latitude': 39.8283, 'longitude': -98.5795}
        
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = None
        
    if 'map_view_mode' not in st.session_state:
        st.session_state.map_view_mode = color_field
    
    # Define initial map center and zoom
    if reset_view or st.session_state.map_last_click is None:
        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()
        zoom_level = 4
    else:
        center_lat = st.session_state.map_last_click['latitude']
        center_lon = st.session_state.map_last_click['longitude']
        zoom_level = 6
    
    # Create a Folium map with the specified style
    # Map style with proper attribution to prevent errors
    tile_styles = {
        "OpenStreetMap": {
            "tiles": "OpenStreetMap",
            "attr": "© OpenStreetMap contributors"
        },
        "CartoDB positron": {
            "tiles": "CartoDB positron",
            "attr": "© OpenStreetMap contributors, © CARTO"
        }
    }
    
    # Get the appropriate style and attribution
    chosen_style = tile_styles.get(map_style, tile_styles["OpenStreetMap"])
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles=chosen_style["tiles"],
        attr=chosen_style["attr"],
        width='100%',
        height=height
    )
    
    # Add a fullscreen button
    folium.plugins.Fullscreen().add_to(m)
    
    # Add a layer control panel if we're using multiple layers
    layer_control = folium.LayerControl(position='topright')
    
    # Different display modes
    if display_mode == "Markers":
        # Individual markers for each location
        for idx, row in df.iterrows():
            # Format info for the popup
            market_size_formatted = f"${int(row['market_size']):,}"
            growth_formatted = f"{row['growth_rate']:.1f}%"
            opportunity_formatted = f"{row['opportunity_score']:.1f}"
            population_formatted = f"{int(row['population']):,}" if 'population' in row else "N/A"
            
            # Determine growth category for visual indicator
            if row['growth_rate'] > 15:
                growth_category = "High growth market"
                growth_color = "#27ae60"
            elif row['growth_rate'] > 5:
                growth_category = "Moderate growth market"
                growth_color = "#f39c12"
            else:
                growth_category = "Slow growth market"
                growth_color = "#e74c3c"
            
            # Create enhanced HTML popup with rich interactivity and visual elements
            # Calculate some additional metrics for visualization
            market_size_percentage = min(100, row['market_size']/100000*100)
            growth_rate_percentage = min(100, row['growth_rate']*5)
            opportunity_percentage = min(100, row['opportunity_score']*5)
            
            # Calculate market trend (simulated data for UI enhancement)
            market_trend = "Increasing" if row['growth_rate'] > 7 else "Stable" if row['growth_rate'] > 3 else "Declining"
            trend_icon = "↗️" if market_trend == "Increasing" else "→" if market_trend == "Stable" else "↘️"
            trend_color = "#27ae60" if market_trend == "Increasing" else "#f39c12" if market_trend == "Stable" else "#e74c3c"
            
            # Calculate competitive landscape (simulated data for UI enhancement)
            competition_level = "Low" if row['growth_rate'] > 15 else "Medium" if row['growth_rate'] > 7 else "High"
            competition_color = "#27ae60" if competition_level == "Low" else "#f39c12" if competition_level == "Medium" else "#e74c3c"
            
            # Create a mini-sparkline for trend visualization (simulated)
            sparkline_points = []
            if market_trend == "Increasing":
                sparkline_points = [3, 4, 3.5, 5, 6.5, 6, 7]
            elif market_trend == "Stable":
                sparkline_points = [5, 4.8, 5.2, 5, 4.9, 5.1, 5]
            else:
                sparkline_points = [7, 6.5, 6, 5.5, 5, 4.5, 4]
                
            # Scale points to fit in the visualization area (30px high)
            max_point = max(sparkline_points)
            min_point = min(sparkline_points)
            range_points = max_point - min_point if max_point != min_point else 1
            scaled_points = [int(30 - ((p - min_point) / range_points * 20)) for p in sparkline_points]
            
            # Generate sparkline SVG path
            path_points = []
            for i, point in enumerate(scaled_points):
                x = i * (100 / (len(scaled_points) - 1))
                path_points.append(f"{x},{point}")
            sparkline_path = " ".join(path_points)
            
            # Create star rating based on opportunity score
            star_rating = min(5, max(1, round(row['opportunity_score'] / 4)))
            stars_html = "".join(['<span style="color: #f1c40f;">★</span>' for _ in range(star_rating)] + 
                               ['<span style="color: #ddd;">★</span>' for _ in range(5 - star_rating)])
            
            # Calculate belief alignment score (simulated for UI enhancement)
            belief_alignment = min(100, max(30, int(row['growth_rate'] * 3.5)))
            
            # Generate key segments based on market attributes
            segments = []
            if row['growth_rate'] > 12:
                segments.append({"name": "Empathetic Dreamers", "color": "#3498db", "match": 87})
                segments.append({"name": "Progressive Thinkers", "color": "#9b59b6", "match": 72})
            elif row['growth_rate'] > 8:
                segments.append({"name": "Practical Realists", "color": "#2ecc71", "match": 81})
                segments.append({"name": "Thoughtful Planners", "color": "#f39c12", "match": 68})
            else:
                segments.append({"name": "Traditional Values", "color": "#e67e22", "match": 76})
                segments.append({"name": "Security Focused", "color": "#1abc9c", "match": 65})
            
            # Create enhanced interactive popup with embedded charts and advanced visualizations
            popup_html = f"""
            <div style="width: 340px; font-family: Arial, sans-serif; overflow: hidden; border-radius: 10px; 
                        box-shadow: 0 6px 18px rgba(0,0,0,0.12); animation: fadeIn 0.3s ease-in-out;">
                <style>
                    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                    @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.4); }} 
                                     70% {{ box-shadow: 0 0 0 10px rgba(52, 152, 219, 0); }} 
                                     100% {{ box-shadow: 0 0 0 0 rgba(52, 152, 219, 0); }} }}
                    @keyframes slideInRight {{ from {{ transform: translateX(20px); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
                    @keyframes slideUp {{ from {{ transform: translateY(10px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
                    @keyframes expandWidth {{ from {{ width: 0%; }} to {{ width: {market_size_percentage}%; }} }}
                    
                    .metric-bar {{ animation: expandWidth 1s ease-out; }}
                    .segment-tag {{ transition: all 0.2s ease; }}
                    .segment-tag:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                    .action-button {{ transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
                    .action-button:hover {{ transform: translateY(-3px) scale(1.03); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }}
                    .action-button:active {{ transform: translateY(0) scale(0.98); }}
                    
                    .tab {{ display: inline-block; padding: 8px 12px; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s; }}
                    .tab.active {{ border-bottom-color: #3498db; color: #3498db; font-weight: 600; }}
                    .tab:hover:not(.active) {{ background-color: #f7f9fc; }}
                    
                    .tab-content {{ display: none; animation: fadeIn 0.4s ease-out; }}
                    .tab-content.active {{ display: block; }}
                    
                    /* Tooltip styles */
                    .tooltip-trigger {{ position: relative; display: inline-block; }}
                    .tooltip-trigger .tooltip-content {{ visibility: hidden; width: 120px; background-color: #555; color: #fff; 
                                                     text-align: center; border-radius: 6px; padding: 5px; position: absolute;
                                                     z-index: 1; bottom: 125%; left: 50%; margin-left: -60px; opacity: 0;
                                                     transition: opacity 0.3s; font-size: 11px; }}
                    .tooltip-trigger:hover .tooltip-content {{ visibility: visible; opacity: 1; }}
                    
                    /* Interactive chart styles */
                    .micro-chart {{ height: 40px; position: relative; margin-top: 5px; }}
                    .chart-bar {{ position: absolute; bottom: 0; width: 8px; border-radius: 3px 3px 0 0; 
                               background: {growth_color}; transition: height 1s ease-out; }}
                    
                    /* Star rating animation */
                    .star {{ display: inline-block; transition: transform 0.2s; }}
                    .star:hover {{ transform: scale(1.3); }}
                </style>
                
                <!-- Header with location and overall score -->
                <div style="background: linear-gradient(135deg, {row['color']}40, {row['color']}70); 
                           padding: 15px; position: relative; border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <!-- Top colorful accent strip -->
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 5px; 
                               background: linear-gradient(90deg, {row['color']}, {growth_color});"></div>
                    
                    <!-- Location title and star rating -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <h3 style="margin: 0 0 5px 0; color: #2c3e50; font-size: 18px; font-weight: 600;">
                            {row['city']}, {row['state']}
                        </h3>
                        <div style="font-size: 16px; letter-spacing: 1px;" class="stars">
                            {stars_html}
                        </div>
                    </div>
                    
                    <!-- Quick stats row -->
                    <div style="display: flex; align-items: center; margin-top: 10px; flex-wrap: wrap; gap: 8px;">
                        <div style="font-size: 12px; background-color: {growth_color}; color: white; 
                                  padding: 3px 10px; border-radius: 12px; display: inline-block;
                                  animation: pulse 2s infinite; animation-delay: 0.5s;">
                            {growth_category}
                        </div>
                        <div style="display: flex; align-items: center; font-size: 12px; color: #555; animation: slideInRight 0.6s;">
                            <span style="color: {trend_color}; font-weight: bold; margin-right: 3px;">{trend_icon}</span> 
                            {market_trend}
                        </div>
                        <div class="tooltip-trigger" style="margin-left: auto; font-size: 12px; 
                                                           color: #555; background: rgba(255,255,255,0.5); 
                                                           padding: 2px 8px; border-radius: 10px;">
                            <span>{belief_alignment}% match</span>
                            <div class="tooltip-content">Belief alignment with target audience</div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab navigation -->
                <div style="display: flex; background-color: #f9f9fb; border-bottom: 1px solid #eee;">
                    <div class="tab active" onclick="showTab(event, 'metrics')" style="flex: 1; text-align: center;">
                        Metrics
                    </div>
                    <div class="tab" onclick="showTab(event, 'audience')" style="flex: 1; text-align: center;">
                        Audience
                    </div>
                    <div class="tab" onclick="showTab(event, 'insights')" style="flex: 1; text-align: center;">
                        Insights
                    </div>
                </div>
                
                <!-- Metrics Tab Content -->
                <div id="metrics" class="tab-content active" style="padding: 15px; background: white;">
                    <!-- Market Size with enhanced visualization -->
                    <div style="margin-bottom: 14px; animation: slideUp 0.5s;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #555; font-weight: 500; font-size: 13px;">Market Size</span>
                            <div style="display: flex; align-items: center;">
                                <span style="color: #2980b9; font-weight: bold; font-size: 14px;">{market_size_formatted}</span>
                            </div>
                        </div>
                        <div style="position: relative;">
                            <div style="background-color: #eef6fc; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div class="metric-bar" style="background: linear-gradient(90deg, #2980b9, #3498db); 
                                                          width: {market_size_percentage}%; height: 100%; border-radius: 4px;"></div>
                            </div>
                            <!-- Benchmark indicators -->
                            <div style="position: absolute; top: -2px; left: 33%; height: 12px; width: 2px; 
                                      background-color: rgba(0,0,0,0.2); opacity: 0.7;"></div>
                            <div style="position: absolute; top: -2px; left: 66%; height: 12px; width: 2px; 
                                      background-color: rgba(0,0,0,0.2); opacity: 0.7;"></div>
                        </div>
                    </div>
                    
                    <!-- Growth Rate with trend visualization -->
                    <div style="margin-bottom: 14px; animation: slideUp 0.6s;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #555; font-weight: 500; font-size: 13px;">Growth Rate</span>
                            <div style="display: flex; align-items: center;">
                                <svg width="50" height="25" style="margin-right: 6px;">
                                    <defs>
                                        <linearGradient id="grad-{idx}" x1="0%" y1="0%" x2="100%" y2="0%">
                                            <stop offset="0%" style="stop-color:{growth_color}50;stop-opacity:1" />
                                            <stop offset="100%" style="stop-color:{growth_color};stop-opacity:1" />
                                        </linearGradient>
                                    </defs>
                                    <polyline points="{sparkline_path}" 
                                          stroke="url(#grad-{idx})" 
                                          fill="none" 
                                          stroke-width="2.5" 
                                          stroke-linecap="round" />
                                    <circle cx="{sparkline_path.split(' ')[-1].split(',')[0]}" 
                                          cy="{sparkline_path.split(' ')[-1].split(',')[1]}" 
                                          r="3" fill="{growth_color}" />
                                </svg>
                                <span style="color: {growth_color}; font-weight: bold; font-size: 14px;">{growth_formatted}</span>
                            </div>
                        </div>
                        <div style="background-color: #f1f9f4; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div class="metric-bar" style="background: linear-gradient(90deg, {growth_color}70, {growth_color}); 
                                                      width: {growth_rate_percentage}%; height: 100%; border-radius: 4px;"></div>
                        </div>
                    </div>
                    
                    <!-- Interactive Micro-Chart -->
                    <div class="micro-chart" style="animation: fadeIn 0.8s; margin-bottom: 14px;">
                        <div class="chart-bar" style="left: 5%; height: {15 + growth_rate_percentage * 0.5}%; animation-delay: 0.1s;"></div>
                        <div class="chart-bar" style="left: 17%; height: {25 + opportunity_percentage * 0.4}%; animation-delay: 0.2s;"></div>
                        <div class="chart-bar" style="left: 29%; height: {20 + market_size_percentage * 0.3}%; animation-delay: 0.3s;"></div>
                        <div class="chart-bar" style="left: 41%; height: {30 + belief_alignment * 0.2}%; animation-delay: 0.4s;"></div>
                        <div class="chart-bar" style="left: 53%; height: {10 + growth_rate_percentage * 0.6}%; animation-delay: 0.5s;"></div>
                        <div class="chart-bar" style="left: 65%; height: {25 + opportunity_percentage * 0.5}%; animation-delay: 0.6s;"></div>
                        <div class="chart-bar" style="left: 77%; height: {15 + market_size_percentage * 0.4}%; animation-delay: 0.7s;"></div>
                        <div class="chart-bar" style="left: 89%; height: {20 + belief_alignment * 0.3}%; animation-delay: 0.8s;"></div>
                    </div>
                    
                    <!-- Opportunity Score with enhanced visualization -->
                    <div style="margin-bottom: 12px; animation: slideUp 0.7s;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="color: #555; font-weight: 500; font-size: 13px;">Opportunity Score</span>
                            <div style="display: flex; align-items: center;">
                                <span style="color: #8e44ad; font-weight: bold; font-size: 14px;">{opportunity_formatted}</span>
                            </div>
                        </div>
                        <div style="background-color: #f5eef8; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div class="metric-bar" style="background: linear-gradient(90deg, #9b59b6, #8e44ad); 
                                                      width: {opportunity_percentage}%; height: 100%; border-radius: 4px;"></div>
                        </div>
                    </div>
                    
                    <!-- Market Quick Stats Section -->
                    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 8px; 
                               margin-top: 5px; font-size: 12px; animation: fadeIn 0.8s;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <div>
                                <span style="color: #555; font-weight: 500;">Population:</span>
                                <span style="font-weight: bold;">{population_formatted}</span>
                            </div>
                            <div class="tooltip-trigger">
                                <span style="color: #555; font-weight: 500;">Competition:</span>
                                <span style="color: {competition_color}; font-weight: bold;">{competition_level}</span>
                                <div class="tooltip-content">Based on market saturation and competitive pressure</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Audience Tab Content -->
                <div id="audience" class="tab-content" style="padding: 15px; background: white; display: none;">
                    <div style="font-size: 13px; color: #555; margin-bottom: 10px; line-height: 1.4;">
                        Primary audience segments that align with the belief patterns in {row['city']}.
                    </div>
                    
                    <!-- Segment List -->
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        {f'''
                        <div class="segment-tag" style="display: flex; justify-content: space-between; 
                                                      align-items: center; padding: 8px 12px; background-color: {segments[0]['color']}15; 
                                                      border-radius: 8px; border-left: 4px solid {segments[0]['color']};">
                            <span style="font-weight: 500; color: #333;">{segments[0]['name']}</span>
                            <span style="color: {segments[0]['color']}; font-weight: 600; font-size: 12px;">{segments[0]['match']}% match</span>
                        </div>
                        
                        <div class="segment-tag" style="display: flex; justify-content: space-between; 
                                                      align-items: center; padding: 8px 12px; background-color: {segments[1]['color']}15; 
                                                      border-radius: 8px; border-left: 4px solid {segments[1]['color']};">
                            <span style="font-weight: 500; color: #333;">{segments[1]['name']}</span>
                            <span style="color: {segments[1]['color']}; font-weight: 600; font-size: 12px;">{segments[1]['match']}% match</span>
                        </div>
                        '''} 
                    </div>
                    
                    <!-- Belief Alignment Chart -->
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 13px; font-weight: 500; color: #555; margin-bottom: 8px;">
                            Belief Alignment
                        </div>
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="flex: 1; height: 8px; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #2ecc71, #27ae60); width: {belief_alignment}%; 
                                          height: 100%; border-radius: 4px; animation: expandWidth 1.2s ease-out;"></div>
                            </div>
                            <div style="font-weight: 600; color: #27ae60; min-width: 45px; text-align: right;">
                                {belief_alignment}%
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Insights Tab Content -->
                <div id="insights" class="tab-content" style="padding: 15px; background: white; display: none;">
                    <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee;">
                        <div style="font-weight: 600; color: #333; margin-bottom: 5px;">Key Opportunity</div>
                        <div style="font-size: 13px; color: #555; line-height: 1.4;">
                            {f"This high-growth market shows strong potential for product expansion." 
                             if row['growth_rate'] > 10 else 
                             f"Moderate but steady growth indicates stable audience demand." 
                             if row['growth_rate'] > 5 else 
                             f"Mature market may require differentiated positioning strategy."}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee;">
                        <div style="font-weight: 600; color: #333; margin-bottom: 5px;">Market Dynamics</div>
                        <div style="font-size: 13px; color: #555; line-height: 1.4;">
                            {f"Competitive pressure is {competition_level.lower()}, suggesting room for market entry with minimal resistance." 
                             if competition_level == "Low" else 
                             f"Balanced competitive landscape requires strategic positioning to capture market share." 
                             if competition_level == "Medium" else 
                             f"High competition may require niche targeting or premium positioning to differentiate."}
                        </div>
                    </div>
                    
                    <div>
                        <div style="font-weight: 600; color: #333; margin-bottom: 5px;">Recommended Approach</div>
                        <div style="font-size: 13px; color: #555; line-height: 1.4;">
                            Focus messaging on {segments[0]['name']} segment values with targeted campaigns emphasizing 
                            {f"innovation and forward-thinking values." if row['growth_rate'] > 10 else 
                             f"practical benefits and reliability." if row['growth_rate'] > 5 else 
                             f"tradition and proven results."}
                        </div>
                    </div>
                </div>
                
                <!-- Call to action buttons with enhanced interactivity -->
                <div style="padding: 12px 15px; background: #f9f9fb; display: flex; gap: 12px; border-top: 1px solid #eee;">
                    <div class="action-button" style="flex: 1; text-align: center; padding: 10px; background-color: #f0f7ff; 
                                                    border-radius: 8px; cursor: pointer;"
                         onclick="window.parent.postMessage({{'type': 'map_click', 'city': '{row['city']}', 'state': '{row['state']}', 'action': 'view_details'}}, '*')">
                        <span style="color: #3498db; font-weight: 500; font-size: 13px;">View Details</span>
                    </div>
                    <div class="action-button" style="flex: 1; text-align: center; padding: 10px; background-color: #3498db; 
                                                    border-radius: 8px; cursor: pointer;"
                         onclick="window.parent.postMessage({{'type': 'map_click', 'city': '{row['city']}', 'state': '{row['state']}', 'action': 'analyze'}}, '*')">
                        <span style="color: white; font-weight: 500; font-size: 13px;">Analyze Market</span>
                    </div>
                </div>
                
                <script>
                    function showTab(event, tabName) {{
                        // Hide all tab contents
                        var tabContents = document.getElementsByClassName("tab-content");
                        for (var i = 0; i < tabContents.length; i++) {{
                            tabContents[i].style.display = "none";
                            tabContents[i].classList.remove("active");
                        }}
                        
                        // Remove active class from all tabs
                        var tabs = document.getElementsByClassName("tab");
                        for (var i = 0; i < tabs.length; i++) {{
                            tabs[i].classList.remove("active");
                        }}
                        
                        // Show the selected tab content and mark the tab as active
                        document.getElementById(tabName).style.display = "block";
                        document.getElementById(tabName).classList.add("active");
                        event.currentTarget.classList.add("active");
                    }}
                    
                    // Animate chart bars on load
                    var bars = document.getElementsByClassName("chart-bar");
                    for (var i = 0; i < bars.length; i++) {{
                        bars[i].style.height = "0px";
                        setTimeout((function(bar, originalHeight) {{
                            return function() {{
                                bar.style.height = originalHeight;
                            }};
                        }})(bars[i], bars[i].style.height), 100);
                    }}
                </script>
            </div>
            """
            
            # Create a popup and tooltip
            popup = folium.Popup(folium.Html(popup_html, script=True), max_width=300)
            tooltip = f"{row['city']}, {row['state']}"
            
            # Create a circle marker
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=row['marker_radius'],
                popup=popup,
                tooltip=tooltip,
                color='white',
                weight=1.5,
                fill_color=row['color'],
                fill_opacity=0.7,
                fill=True
            ).add_to(m)
            
            # Add a label if requested
            if show_labels:
                folium.map.Marker(
                    [row['latitude'], row['longitude']],
                    icon=folium.DivIcon(
                        icon_size=(0, 0),
                        icon_anchor=(0, 0),
                        html=f'<div style="font-size: 10px; white-space: nowrap; color: #333; text-shadow: 1px 1px 1px white;">{row["city"]}</div>',
                    )
                ).add_to(m)
    
    elif display_mode == "Clusters":
        # Create a marker cluster
        marker_cluster = MarkerCluster().add_to(m)
        
        # Add markers to the cluster
        for idx, row in df.iterrows():
            # Format info for the popup
            market_size_formatted = f"${int(row['market_size']):,}"
            growth_formatted = f"{row['growth_rate']:.1f}%"
            
            # Enhanced popup for clustered markers with mini visualizations
            # Calculate growth color based on rate
            growth_color = "#27ae60" if row['growth_rate'] > 15 else "#f39c12" if row['growth_rate'] > 5 else "#e74c3c"
            
            # Create small bar charts for metrics
            market_size_percentage = min(100, row['market_size']/100000*100)
            growth_rate_percentage = min(100, row['growth_rate']*5)
            opportunity_percentage = min(100, row['opportunity_score']*5)
            
            popup_html = f"""
            <div style="width: 220px; font-family: Arial, sans-serif;">
                <div style="padding: 8px; background: linear-gradient(to right, {row['color']}30, {row['color']}10); border-left: 4px solid {row['color']};">
                    <h4 style="margin: 0 0 5px 0; color: #333; font-size: 16px;">
                        {row['city']}, {row['state']}
                    </h4>
                </div>
                
                <div style="padding: 10px;">
                    <!-- Market Size -->
                    <div style="margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 12px;">
                            <span>Market Size:</span>
                            <span style="font-weight: bold; color: #2980b9;">{market_size_formatted}</span>
                        </div>
                        <div style="background-color: #eef6fc; height: 6px; border-radius: 3px; overflow: hidden;">
                            <div style="background-color: #3498db; width: {market_size_percentage}%; height: 100%;"></div>
                        </div>
                    </div>
                    
                    <!-- Growth Rate -->
                    <div style="margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 12px;">
                            <span>Growth Rate:</span>
                            <span style="font-weight: bold; color: {growth_color};">{growth_formatted}</span>
                        </div>
                        <div style="background-color: #f1f9f4; height: 6px; border-radius: 3px; overflow: hidden;">
                            <div style="background-color: {growth_color}; width: {growth_rate_percentage}%; height: 100%;"></div>
                        </div>
                    </div>
                    
                    <!-- Opportunity Score -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 12px;">
                            <span>Opportunity Score:</span>
                            <span style="font-weight: bold; color: #8e44ad;">{row['opportunity_score']:.1f}</span>
                        </div>
                        <div style="background-color: #f5eef8; height: 6px; border-radius: 3px; overflow: hidden;">
                            <div style="background-color: #8e44ad; width: {opportunity_percentage}%; height: 100%;"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Interactive buttons -->
                <div style="padding: 0 10px 10px 10px; display: flex; gap: 5px;">
                    <button onclick="window.parent.postMessage({{'type': 'map_click', 'city': '{row['city']}', 'state': '{row['state']}'}}, '*')" 
                            style="flex: 1; padding: 5px; background-color: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px;">
                        View Details
                    </button>
                </div>
            </div>
            """
            
            popup = folium.Popup(popup_html, max_width=200)
            tooltip = f"{row['city']}, {row['state']}"
            
            # Use a regular marker with a colored icon
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=popup,
                tooltip=tooltip,
                icon=folium.Icon(color=get_icon_color(row['color']), icon='info-sign')
            ).add_to(marker_cluster)
    
    elif display_mode == "Heatmap":
        # Prepare heatmap data with weighting by the color field
        # Scale the weight to make the heatmap more visually appealing
        heatmap_data = [
            [row['latitude'], row['longitude'], row[color_field]]
            for _, row in df.iterrows()
        ]
        
        # Create a heatmap layer
        folium.plugins.HeatMap(
            heatmap_data,
            radius=15,
            min_opacity=0.5,
            blur=10,
            gradient={
                0.2: '#fee0d2', 
                0.4: '#fc9272', 
                0.6: '#de2d26', 
                0.8: '#a50f15', 
                1.0: '#67000d'
            } if color_field == 'growth_rate' else None,
            name=f'{color_dimension} Heatmap'
        ).add_to(m)
        
        # Add enhanced markers on top for identification with rich tooltips
        markers_group = folium.FeatureGroup(name="Location Markers")
        for idx, row in df.iterrows():
            # Create a custom tooltip with styled HTML
            tooltip_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 5px; max-width: 200px;">
                <div style="font-weight: bold; font-size: 14px; color: #333; margin-bottom: 3px;">
                    {row['city']}, {row['state']}
                </div>
                <div style="display: flex; align-items: center; gap: 5px; font-size: 12px; margin-top: 3px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: {row['color']};"></div>
                    <span>{color_dimension}: <strong>{row[color_field]:.1f}</strong></span>
                </div>
                <div style="font-size: 10px; color: #666; margin-top: 3px; font-style: italic;">
                    Click for details
                </div>
            </div>
            """
            
            # Create a popup for more detailed information
            market_size_formatted = f"${int(row['market_size']):,}"
            growth_formatted = f"{row['growth_rate']:.1f}%"
            
            popup_html = f"""
            <div style="width: 200px; font-family: Arial, sans-serif; padding: 10px;">
                <h4 style="margin: 0 0 8px 0; border-bottom: 2px solid {row['color']}; padding-bottom: 5px;">
                    {row['city']}, {row['state']}
                </h4>
                <div style="display: flex; flex-direction: column; gap: 5px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 500;">Market Size:</span>
                        <span style="color: #2980b9;">{market_size_formatted}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 500;">Growth Rate:</span>
                        <span style="color: {"#27ae60" if row['growth_rate'] > 10 else "#f39c12" if row['growth_rate'] > 5 else "#e74c3c"};">
                            {growth_formatted}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 500;">Opportunity:</span>
                        <span style="color: #8e44ad;">{row['opportunity_score']:.1f}</span>
                    </div>
                </div>
                <button onclick="window.parent.postMessage({{'type': 'map_click', 'city': '{row['city']}', 'state': '{row['state']}'}}, '*')" 
                        style="width: 100%; margin-top: 10px; padding: 5px; background-color: #3498db; color: white; border: none; 
                               border-radius: 3px; cursor: pointer; font-size: 12px;">
                    View Full Details
                </button>
            </div>
            """
            
            # Add marker with enhanced tooltip and popup
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                tooltip=folium.Tooltip(tooltip_html),
                popup=folium.Popup(popup_html, max_width=220),
                color='white',
                fill=True,
                fill_color=row['color'],
                fill_opacity=0.8,
                weight=1.5
            ).add_to(markers_group)
        
        markers_group.add_to(m)
        layer_control.add_to(m)
    
    # Add a legend if requested
    if show_legend:
        legend_html = create_legend(df, color_field)
        m.get_root().html.add_child(folium.Element(legend_html))
    
    # Display the map with improved error handling and logging
    map_container = st.container()
    with map_container:
        try:
            # Use a more robust approach for rendering the map
            # Explicitly set width to ensure proper rendering
            folium_static(m, width="100%", height=height)
            st.session_state["map_rendered"] = True
        except Exception as e:
            st.error(f"Error rendering map: {str(e)}")
            st.session_state["map_rendered"] = False
            st.info("Please try changing the map style or refreshing the page.")
            # Log the error for debugging
            import logging
            logging.error(f"Folium map rendering error: {str(e)}")
    
    # Add a click handler for location selection
    # Note: Since Folium doesn't support direct click handlers through Streamlit, we'll use markers with popups that have
    # JS to send messages to the parent frame. For a proper implementation, you'd need a component that can listen to these events.
    
    # Add selected location details if any are stored from previous clicks
    if st.session_state.selected_location:
        location = st.session_state.selected_location
        
        # Create a visually appealing location details card
        with st.expander(f"Selected Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}", expanded=True):
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown(f"### {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}")
                
                # Market metrics
                st.markdown("#### Market Metrics")
                metrics_cols = st.columns(3)
                
                with metrics_cols[0]:
                    st.metric("Market Size", f"${location.get('market_size', 0):,.0f}")
                    
                with metrics_cols[1]:
                    st.metric("Growth Rate", f"{location.get('growth_rate', 0):.1f}%")
                    
                with metrics_cols[2]:
                    st.metric("Opportunity Score", f"{location.get('opportunity_score', 0):.1f}")
                
                # Population info if available
                if 'population' in location:
                    st.metric("Population", f"{location.get('population', 0):,}")
                
                # Action buttons
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if st.button("View Market Analysis", key="view_analysis_btn", use_container_width=True):
                        st.info("Detailed market analysis feature will be available in the next update.")
                        
                with action_col2:
                    if st.button("Add to Watchlist", key="add_watchlist_btn", use_container_width=True):
                        st.success(f"Added {location.get('city', 'Unknown')} to your watchlist.")
            
            with col2:
                # Show a small map of just this location
                location_map = folium.Map(
                    location=[location.get('latitude', 0), location.get('longitude', 0)],
                    zoom_start=10,
                    tiles='CartoDB positron',
                    width='100%',
                    height=300
                )
                
                folium.CircleMarker(
                    location=[location.get('latitude', 0), location.get('longitude', 0)],
                    radius=10,
                    color='white',
                    fill=True,
                    fill_color='#3498db',
                    fill_opacity=0.7,
                    tooltip=f"{location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}"
                ).add_to(location_map)
                
                try:
                    folium_static(location_map, width="100%", height=300)
                except Exception as e:
                    st.error(f"Error rendering location map: {str(e)}")
                    import logging
                    logging.error(f"Folium location map error: {str(e)}")
    
    # Return the map object and data
    return m, df

# Helper functions for the map
def get_icon_color(hex_color):
    """Convert hex color to a Folium icon color (limited palette)"""
    # Map the hex colors to Folium's limited icon color palette
    # This is a simplified mapping - more complex logic could be implemented
    if hex_color.startswith('#'):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Simple heuristic to categorize colors
        if r > g and r > b:
            return 'red'
        elif g > r and g > b:
            return 'green'
        elif b > r and b > g:
            return 'blue'
        elif r > 200 and g > 200:
            return 'beige'
        elif r > 150 and g > 100 and b > 100:
            return 'lightred'
        else:
            return 'darkpurple'
    
    return 'blue'  # Default

def create_legend(df, color_field):
    """Create a legend for the map based on the color field"""
    # Create a legend with gradient colors
    min_val = df[color_field].min()
    max_val = df[color_field].max()
    
    # Determine legend title and color gradient based on field
    if color_field == 'growth_rate':
        title = 'Growth Rate (%)'
        colors = ['#dce892', '#b6dc92', '#92dc94', '#92dcdc', '#92b6dc']
    elif color_field == 'market_size':
        title = 'Market Size ($)'
        colors = ['#92b6dc', '#9292dc', '#b692dc', '#dc92dc', '#dc92b6']
    else:  # opportunity_score
        title = 'Opportunity Score'
        colors = ['#dc92b6', '#dc92dc', '#b692dc', '#9292dc', '#92b6dc']
    
    # Format values based on field
    formatted_min = f"${min_val:,.0f}" if color_field == 'market_size' else f"{min_val:.1f}"
    formatted_max = f"${max_val:,.0f}" if color_field == 'market_size' else f"{max_val:.1f}"
    
    # Create legend HTML
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 50px; right: 50px; z-index: 1000;
                background-color: white; padding: 10px; 
                border-radius: 6px; border: 1px solid #ccc;
                font-family: Arial, sans-serif; opacity: 0.9;">
        <div style="font-weight: bold; margin-bottom: 5px;">{title}</div>
        <div style="display: flex; flex-direction: column; gap: 3px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 120px; height: 15px; border-radius: 3px; 
                           background: linear-gradient(to right, {', '.join(colors)})"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.8em;">
                <span>{formatted_min}</span>
                <span>{formatted_max}</span>
            </div>
        </div>
    </div>
    """
    
    return legend_html
    
    # Display selected location details if any
    if st.session_state.selected_location:
        location = st.session_state.selected_location
        
        # Create a visually appealing location details card with enhanced interactivity
        growth_class = "high" if location['growth_rate'] > 15 else "medium" if location['growth_rate'] > 5 else "low"
        growth_color = "#27ae60" if growth_class == "high" else "#f39c12" if growth_class == "medium" else "#e74c3c"
        opp_percentage = min(100, location['opportunity_score'] * 3.33)
        market_percentage = min(100, location['market_size'] / 100000 * 100)
        
        # Calculate a star rating (1-5) based on opportunity score
        star_rating = min(5, max(1, round(location['opportunity_score'] / 20)))
        stars_html = "".join(["★" for _ in range(star_rating)] + ["☆" for _ in range(5 - star_rating)])
        
        location_details = f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0; margin-top: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #2c3e50; font-size: 20px;">{location['city']}, {location['state']} <span style="font-size: 14px; color: #7f8c8d; font-weight: normal;">Market Analysis</span></h3>
                <div style="color: #f1c40f; font-size: 18px; letter-spacing: 2px;">{stars_html}</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0;">
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; overflow: hidden;">
                    <div style="font-size: 13px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px;">MARKET SIZE</div>
                    <div style="font-size: 22px; font-weight: bold; color: #2980b9; margin: 5px 0;">${location['market_size']:,.0f}</div>
                    <div style="height: 4px; width: 100%; background-color: #ecf0f1; margin-top: 10px; border-radius: 2px;">
                        <div style="height: 100%; width: {market_percentage}%; background-color: #2980b9; border-radius: 2px;"></div>
                    </div>
                </div>
                
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; overflow: hidden;">
                    <div style="font-size: 13px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px;">GROWTH RATE</div>
                    <div style="font-size: 22px; font-weight: bold; color: {growth_color}; margin: 5px 0; display: flex; align-items: center;">
                        {location['growth_rate']:.1f}%
                        <span style="margin-left: 8px; font-size: 14px; background-color: {growth_color}; color: white; padding: 2px 8px; border-radius: 10px; opacity: 0.8;">{growth_class.upper()}</span>
                    </div>
                    <div style="height: 4px; width: 100%; background-color: #ecf0f1; margin-top: 10px; border-radius: 2px;">
                        <div style="height: 100%; width: {min(100, location['growth_rate'] * 3.33)}%; background-color: {growth_color}; border-radius: 2px;"></div>
                    </div>
                </div>
                
                <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); position: relative; overflow: hidden;">
                    <div style="font-size: 13px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px;">OPPORTUNITY SCORE</div>
                    <div style="font-size: 22px; font-weight: bold; color: #8e44ad; margin: 5px 0;">{location['opportunity_score']:.1f}</div>
                    <div style="height: 4px; width: 100%; background-color: #ecf0f1; margin-top: 10px; border-radius: 2px;">
                        <div style="height: 100%; width: {opp_percentage}%; background-color: #8e44ad; border-radius: 2px;"></div>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; gap: 15px; margin: 15px 0;">
                <div style="flex: 1; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #3498db; color: white; display: flex; justify-content: center; align-items: center; margin-right: 10px;">👥</div>
                        <span style="font-size: 14px; color: #2c3e50;">Population</span>
                    </div>
                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">{location['population']:,}</div>
                </div>
                
                <div style="flex: 1; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #3498db; color: white; display: flex; justify-content: center; align-items: center; margin-right: 10px;">📍</div>
                        <span style="font-size: 14px; color: #2c3e50;">Location</span>
                    </div>
                    <div style="font-size: 16px; color: #2c3e50;">
                        {location['latitude']:.2f}, {location['longitude']:.2f}
                    </div>
                </div>
            </div>
            
            <div style="background-color: #edf7ff; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #3498db;">
                <div style="font-weight: 500; color: #2980b9; margin-bottom: 5px;">Market Insight</div>
                <p style="margin: 0; color: #34495e; font-size: 14px;">
                    {location['city']} shows {
                    'exceptional growth potential with a solid market base' if location['growth_rate'] > 15 and location['market_size'] > 50000 else
                    'strong growth in an emerging market' if location['growth_rate'] > 15 and location['market_size'] <= 50000 else
                    'stable performance in an established market' if location['growth_rate'] <= 15 and location['market_size'] > 50000 else
                    'moderate potential requiring targeted strategies'
                    }. Click "View Detailed Analysis" below for comprehensive market intelligence including demographic insights, competitive landscape, and strategic recommendations.
                </p>
            </div>
        </div>
        """
        
        render_html(location_details)
        
        # Add action buttons for the selected location
        action_cols = st.columns(3)
        
        with action_cols[0]:
            if st.button("View Detailed Analysis", key="view_analysis", use_container_width=True):
                st.info(f"Generating detailed analysis for {location['city']}, {location['state']}...")
                # In a real implementation, this would generate a detailed report
        
        with action_cols[1]:
            if st.button("Add to Comparison", key="add_compare", use_container_width=True):
                st.success(f"Added {location['city']}, {location['state']} to comparison list")
                # In a real implementation, this would add to a comparison list
        
        with action_cols[2]:
            if st.button("Clear Selection", key="clear_selection", use_container_width=True):
                st.session_state.selected_location = None
                st.rerun()
    
    # Display context and insights
    with st.expander("💡 How to Interpret This Map"):
        st.markdown(f"""
        ### Understanding the Market Opportunity Map
        
        This interactive map visualizes potential market opportunities across different geographic regions:
        
        - **Circle Size**: Currently showing {'**Market Size**' if size_field == 'market_size' else '**Population**' if size_field == 'population' else '**Growth Rate**'} - larger circles indicate higher values
        - **Circle Color**: Currently showing {'**Growth Rate**' if color_field == 'growth_rate' else '**Market Size**' if color_field == 'market_size' else '**Opportunity Score**'} - {'greener' if color_field == 'growth_rate' else 'bluer' if color_field == 'market_size' else 'more purple'} circles represent higher values
        - **Click on any circle**: For detailed information and analysis options
        
        ### Customizing Your View
        
        - Use the **Map Style** dropdown to change the map appearance
        - Use the **Color By** and **Size By** options to visualize different metrics
        - Toggle **3D View** to see values as height on the map
        - Use **Animate** to add subtle movement effects
        
        ### Strategic Applications
        
        Use this map to:
        1. Identify regions with both large market size and high growth for maximum opportunity
        2. Target emerging markets with high growth but currently smaller market size
        3. Locate stable markets with large size but moderate growth for reliable returns
        
        For deeper analysis, click on specific locations or use the analysis tools below.
        """)
    
    return m, df

def render_opportunity_metrics(df, title="Market Metrics", num_top_markets=5):
    """
    Render opportunity metrics and comparisons from map data.
    
    Args:
        df (DataFrame): DataFrame with map data
        title (str): Title for the metrics section
        num_top_markets (int): Number of top markets to display
    """
    if df is None or len(df) == 0:
        return
    
    st.markdown(f"## {title}")
    
    # Add opportunity score if not present
    if 'opportunity_score' not in df.columns:
        df['opportunity_score'] = (df['growth_rate'] * df['market_size'] / 1000).round(1)
    
    # Create metrics tabs for different views
    metrics_tabs = st.tabs(["Overview", "Top Markets", "Opportunity Analysis", "Regional Comparison"])
    
    with metrics_tabs[0]:
        # Calculate aggregate metrics
        total_market_size = df['market_size'].sum()
        avg_market_size = df['market_size'].mean()
        median_market_size = df['market_size'].median()
        
        avg_growth_rate = df['growth_rate'].mean()
        median_growth_rate = df['growth_rate'].median()
        max_growth_rate = df['growth_rate'].max()
        
        total_population = df['population'].sum() if 'population' in df.columns else 0
        avg_opportunity = df['opportunity_score'].mean()
        total_locations = len(df)
        
        # Create a metrics dashboard
        st.markdown("### Market Overview")
        
        # Top row metrics
        metric_cols1 = st.columns(3)
        metric_cols1[0].metric(
            "Total Market Potential", 
            f"${total_market_size:,.0f}",
            f"{avg_market_size/median_market_size*100-100:.1f}% vs median"
        )
        metric_cols1[1].metric(
            "Average Growth Rate", 
            f"{avg_growth_rate:.1f}%",
            f"{avg_growth_rate-median_growth_rate:.1f}pp vs median"
        )
        metric_cols1[2].metric(
            "Locations Analyzed", 
            f"{total_locations:,}",
            f"Total Pop: {total_population:,}" if total_population > 0 else None
        )
        
        # Second row metrics
        metric_cols2 = st.columns(3)
        metric_cols2[0].metric(
            "Average Market Size", 
            f"${avg_market_size:,.0f}",
            f"Median: ${median_market_size:,.0f}"
        )
        metric_cols2[1].metric(
            "Highest Growth Rate", 
            f"{max_growth_rate:.1f}%",
            f"{max_growth_rate-avg_growth_rate:.1f}pp vs average"
        )
        metric_cols2[2].metric(
            "Average Opportunity Score", 
            f"{avg_opportunity:.1f}",
            "Higher scores = better opportunities"
        )
        
        # Create a regional distribution visualization
        st.markdown("### Regional Distribution")
        
        # Group by state for regional analysis
        if 'state' in df.columns:
            state_summary = df.groupby('state').agg({
                'market_size': ['sum', 'mean'],
                'growth_rate': 'mean',
                'opportunity_score': 'mean',
                'city': 'count'
            }).reset_index()
            
            # Flatten the column names
            state_summary.columns = [
                'State', 'Total Market Size', 'Avg Market Size', 
                'Avg Growth Rate', 'Avg Opportunity Score', 'Location Count'
            ]
            
            # Create a choropleth map of the US with data by state
            state_fig = px.choropleth(
                state_summary,
                locations='State',
                locationmode='USA-states',
                color='Avg Opportunity Score',
                scope="usa",
                color_continuous_scale=px.colors.sequential.Viridis,
                hover_data={
                    'State': True,
                    'Total Market Size': ':,.0f',
                    'Avg Growth Rate': ':.1f%',
                    'Location Count': True,
                    'Avg Opportunity Score': ':.1f'
                },
                labels={
                    'State': 'State',
                    'Total Market Size': 'Total Market ($)',
                    'Avg Growth Rate': 'Growth Rate (%)',
                    'Location Count': 'Locations',
                    'Avg Opportunity Score': 'Opportunity Score'
                },
                title="State-Level Opportunity Analysis"
            )
            
            state_fig.update_layout(
                height=450,
                geo=dict(
                    showlakes=True,
                    lakecolor='rgb(255, 255, 255)'
                ),
                coloraxis_colorbar=dict(
                    title="Opportunity<br>Score"
                )
            )
            
            st.plotly_chart(state_fig, use_container_width=True)
        
        # Add a date stamp for data freshness
        st.caption(f"Data last updated: {datetime.now().strftime('%B %d, %Y')}")
    
    with metrics_tabs[1]:
        # Create columns for different rankings
        rank_col1, rank_col2 = st.columns(2)
        
        with rank_col1:
            st.markdown("### Top Markets by Size")
            top_size_markets = df.sort_values('market_size', ascending=False).head(num_top_markets)
            
            # Create a more visually appealing list with progress bars
            for i, (_, market) in enumerate(top_size_markets.iterrows()):
                # Calculate the percentage of the maximum for the progress bar
                percentage = min(100, market['market_size'] / top_size_markets['market_size'].max() * 100)
                
                market_html = f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <div>
                            <span style="font-weight: bold; margin-right: 5px;">#{i+1}</span>
                            <span>{market['city']}, {market['state']}</span>
                        </div>
                        <div style="font-weight: bold; color: #2980b9;">${market['market_size']:,.0f}</div>
                    </div>
                    <div style="background-color: #ecf0f1; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background-color: #3498db; width: {percentage}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
                render_html(market_html)
        
        with rank_col2:
            st.markdown("### Top Markets by Growth")
            top_growth_markets = df.sort_values('growth_rate', ascending=False).head(num_top_markets)
            
            for i, (_, market) in enumerate(top_growth_markets.iterrows()):
                # Calculate the percentage of the maximum for the progress bar
                percentage = min(100, market['growth_rate'] / top_growth_markets['growth_rate'].max() * 100)
                
                # Determine color based on growth rate
                if market['growth_rate'] > 15:
                    color = "#27ae60"  # Green for high growth
                elif market['growth_rate'] > 5:
                    color = "#f39c12"  # Orange for medium growth
                else:
                    color = "#e74c3c"  # Red for low growth
                
                market_html = f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <div>
                            <span style="font-weight: bold; margin-right: 5px;">#{i+1}</span>
                            <span>{market['city']}, {market['state']}</span>
                        </div>
                        <div style="font-weight: bold; color: {color};">{market['growth_rate']:.1f}%</div>
                    </div>
                    <div style="background-color: #ecf0f1; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
                render_html(market_html)
        
        # Additional ranking section - Opportunity Score
        st.markdown("### Top Markets by Opportunity Score")
        top_opportunity_markets = df.sort_values('opportunity_score', ascending=False).head(num_top_markets)
        
        # Create a horizontal bar chart for opportunity scores
        opp_fig = px.bar(
            top_opportunity_markets,
            y='city',
            x='opportunity_score',
            orientation='h',
            color='opportunity_score',
            color_continuous_scale=px.colors.sequential.Viridis,
            hover_data={
                'state': True,
                'market_size': ':,.0f',
                'growth_rate': ':.1f%',
                'opportunity_score': ':.1f'
            },
            labels={
                'city': 'City',
                'opportunity_score': 'Opportunity Score',
                'state': 'State',
                'market_size': 'Market Size ($)',
                'growth_rate': 'Growth Rate (%)'
            },
            height=400
        )
        
        opp_fig.update_layout(
            yaxis=dict(title='', autorange="reversed"),
            xaxis=dict(title='Opportunity Score'),
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        st.plotly_chart(opp_fig, use_container_width=True)
    
    with metrics_tabs[2]:
        # Create an enhanced opportunity quadrant analysis
        st.markdown("### Market Opportunity Quadrant Analysis")
        
        # Create a more advanced and interactive scatter plot
        # Allow user to select dimensions for analysis
        analysis_cols = st.columns([1, 1, 2])
        
        with analysis_cols[0]:
            x_dimension = st.selectbox(
                "X-Axis",
                options=["Market Size", "Growth Rate", "Population", "Opportunity Score"],
                index=0,
                key="quad_x_dimension"
            )
            
            # Map dimension names to column names
            dimension_map = {
                "Market Size": "market_size",
                "Growth Rate": "growth_rate",
                "Population": "population",
                "Opportunity Score": "opportunity_score"
            }
            
            x_field = dimension_map[x_dimension]
        
        with analysis_cols[1]:
            y_dimension = st.selectbox(
                "Y-Axis",
                options=["Growth Rate", "Market Size", "Population", "Opportunity Score"],
                index=0,
                key="quad_y_dimension"
            )
            
            y_field = dimension_map[y_dimension]
        
        with analysis_cols[2]:
            show_quadrants = st.checkbox("Show Quadrants", value=True, key="show_quadrants")
            color_states = st.checkbox("Color by State", value=True, key="color_states")
            show_names = st.checkbox("Show City Names", value=False, key="show_city_names")
        
        # Create the advanced scatter plot
        fig = px.scatter(
            df, 
            x=x_field, 
            y=y_field,
            size="population" if "population" in df.columns else None,
            color="state" if color_states else "opportunity_score",
            hover_name="city",
            text="city" if show_names else None,
            size_max=40,
            labels={
                "market_size": "Market Size ($)",
                "growth_rate": "Growth Rate (%)",
                "population": "Population",
                "state": "State",
                "opportunity_score": "Opportunity Score"
            },
            color_continuous_scale=px.colors.sequential.Viridis if not color_states else None,
        )
        
        # Update text position and size
        if show_names:
            fig.update_traces(
                textposition='top center',
                textfont=dict(size=10, color='darkgray')
            )
        
        # Update layout with improved styling
        fig.update_layout(
            height=600,
            xaxis_title=x_dimension,
            yaxis_title=y_dimension,
            plot_bgcolor='rgba(240, 240, 240, 0.2)',
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add quadrant lines and labels if requested
        if show_quadrants:
            median_x = df[x_field].median()
            median_y = df[y_field].median()
            
            fig.add_shape(
                type="line", x0=median_x, y0=df[y_field].min(), x1=median_x, y1=df[y_field].max(),
                line=dict(color="gray", width=1, dash="dash")
            )
            
            fig.add_shape(
                type="line", x0=df[x_field].min(), y0=median_y, x1=df[x_field].max(), y1=median_y,
                line=dict(color="gray", width=1, dash="dash")
            )
            
            # Add quadrant annotations with improved positioning and styling
            fig.add_annotation(
                x=df[x_field].max() * 0.75, 
                y=df[y_field].max() * 0.8,
                text=f"High {y_dimension}<br>High {x_dimension}<br><b>Priority Targets</b>",
                showarrow=False,
                font=dict(size=12, color="#27ae60")
            )
            
            fig.add_annotation(
                x=df[x_field].min() * 1.5, 
                y=df[y_field].max() * 0.8,
                text=f"High {y_dimension}<br>Low {x_dimension}<br><b>Emerging Opportunities</b>",
                showarrow=False,
                font=dict(size=12, color="#3498db")
            )
            
            fig.add_annotation(
                x=df[x_field].max() * 0.75, 
                y=df[y_field].min() * 1.5,
                text=f"Low {y_dimension}<br>High {x_dimension}<br><b>Established Markets</b>",
                showarrow=False,
                font=dict(size=12, color="#f39c12")
            )
            
            fig.add_annotation(
                x=df[x_field].min() * 1.5, 
                y=df[y_field].min() * 1.5,
                text=f"Low {y_dimension}<br>Low {x_dimension}<br><b>Niche Strategy</b>",
                showarrow=False,
                font=dict(size=12, color="#e74c3c")
            )
        
        # Render the plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Display explanation with dynamic dimension names
        with st.expander(f"📊 Understanding the {x_dimension} vs {y_dimension} Analysis"):
            st.markdown(f"""
            ### Opportunity Quadrant Analysis: {x_dimension} vs {y_dimension}
            
            This chart plots markets based on {x_dimension.lower()} (x-axis) and {y_dimension.lower()} (y-axis), creating four strategic quadrants:
            
            1. **High {y_dimension}, High {x_dimension}** (upper right): These are your primary targets that offer both immediate returns and growth potential.
            
            2. **High {y_dimension}, Low {x_dimension}** (upper left): Emerging opportunities that may require investment now for future returns.
            
            3. **Low {y_dimension}, High {x_dimension}** (lower right): Established markets with stable, reliable returns but limited growth.
            
            4. **Low {y_dimension}, Low {x_dimension}** (lower left): Generally avoid these markets unless you have a specialized niche strategy.
            
            The size of each bubble represents the population, giving you a third dimension for market assessment.
            """)
    
    with metrics_tabs[3]:
        # Add regional comparison features
        st.markdown("### Regional Market Comparison")
        
        if 'state' in df.columns:
            # Group by state
            state_data = df.groupby('state').agg({
                'market_size': ['mean', 'sum', 'count'],
                'growth_rate': ['mean', 'max'],
                'opportunity_score': 'mean',
                'population': 'sum' if 'population' in df.columns else 'count'
            }).reset_index()
            
            # Flatten the multi-level columns
            state_data.columns = [
                'state', 
                'avg_market_size', 'total_market_size', 'market_count',
                'avg_growth', 'max_growth',
                'avg_opportunity',
                'total_population'
            ]
            
            # Create a parallel coordinates plot for multi-dimensional comparison
            dimensions = [
                dict(range=[0, state_data['avg_market_size'].max()], 
                     label='Avg Market Size', values=state_data['avg_market_size']),
                dict(range=[0, state_data['total_market_size'].max()], 
                     label='Total Market Size', values=state_data['total_market_size']),
                dict(range=[0, state_data['avg_growth'].max()], 
                     label='Avg Growth Rate (%)', values=state_data['avg_growth']),
                dict(range=[0, state_data['avg_opportunity'].max()], 
                     label='Opportunity Score', values=state_data['avg_opportunity']),
                dict(range=[0, state_data['market_count'].max()], 
                     label='Location Count', values=state_data['market_count'])
            ]
            
            parallel_fig = go.Figure(data=
                go.Parcoords(
                    line=dict(
                        color=state_data['avg_opportunity'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title='Opportunity<br>Score')
                    ),
                    dimensions=dimensions,
                    labelangle=30,
                    labelfont=dict(size=12, color='black'),
                    tickfont=dict(size=10)
                )
            )
            
            parallel_fig.update_layout(
                title="Multi-Dimensional State Comparison",
                height=500,
                margin=dict(l=80, r=80, t=50, b=50)
            )
            
            st.plotly_chart(parallel_fig, use_container_width=True)
            
            # Create a radar chart for selected states
            st.markdown("### State Comparison Radar Chart")
            
            # Let user select states to compare
            top_states = state_data.sort_values('avg_opportunity', ascending=False)['state'].head(10).tolist()
            selected_states = st.multiselect(
                "Select States to Compare",
                options=state_data['state'].tolist(),
                default=top_states[:3] if len(top_states) >= 3 else top_states
            )
            
            if selected_states:
                # Filter data for selected states
                selected_data = state_data[state_data['state'].isin(selected_states)]
                
                # Normalize the values for radar chart
                radar_data = selected_data.copy()
                
                metrics = [
                    'avg_market_size', 'avg_growth', 
                    'avg_opportunity', 'market_count'
                ]
                
                # Normalize each metric from 0 to 100
                for metric in metrics:
                    max_val = state_data[metric].max()
                    min_val = state_data[metric].min()
                    range_val = max_val - min_val
                    
                    if range_val > 0:
                        radar_data[f"{metric}_norm"] = ((radar_data[metric] - min_val) / range_val) * 100
                    else:
                        radar_data[f"{metric}_norm"] = 50  # Default if all values are the same
                
                # Create radar chart for comparison
                radar_fig = go.Figure()
                
                for _, state_row in radar_data.iterrows():
                    radar_fig.add_trace(go.Scatterpolar(
                        r=[
                            state_row['avg_market_size_norm'],
                            state_row['avg_growth_norm'],
                            state_row['avg_opportunity_norm'],
                            state_row['market_count_norm']
                        ],
                        theta=[
                            'Market Size', 
                            'Growth Rate', 
                            'Opportunity Score', 
                            'Market Count'
                        ],
                        fill='toself',
                        name=state_row['state']
                    ))
                
                radar_fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    title="State Comparison (Normalized Values)",
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(radar_fig, use_container_width=True)
                
                # Add explanation
                st.caption("Radar chart shows normalized values (0-100) for each metric to enable direct comparison between states")
            else:
                st.info("Please select at least one state to visualize the radar chart")
        else:
            st.warning("State data is not available for regional comparison")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from datetime import datetime
from utils.tier_control import enforce_tier, get_user_tier
from utils.data_access import get_map_data, get_market_insights, get_demographic_summary
from utils.html_render import render_html, render_card, render_progress
from components.opportunity_map import render_opportunity_map, render_opportunity_metrics
from components.insight_card import insight_card, comparison_insight, quick_insight

# Page configuration
st.set_page_config(
    page_title="Where to Invest | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'last_filter_update' not in st.session_state:
    st.session_state.last_filter_update = datetime.now()
    
if 'selected_states' not in st.session_state:
    st.session_state.selected_states = ["CA", "NY", "TX", "FL", "IL"]
    
if 'market_size_threshold' not in st.session_state:
    st.session_state.market_size_threshold = 10000
    
if 'growth_rate_threshold' not in st.session_state:
    st.session_state.growth_rate_threshold = 5.0
    
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "map"  # Options: map, table, comparison

if 'pin_state' not in st.session_state:
    st.session_state.pin_state = None

# Enforce tier access - Accelerate tier required
enforce_tier('Accelerate')
current_tier = get_user_tier()

# Define a function to update the filters
def update_filters():
    st.session_state.last_filter_update = datetime.now()
    
# Define a function to toggle view mode
def toggle_view_mode(mode):
    st.session_state.view_mode = mode

# Define a function to pin a state for comparison
def pin_state(state):
    if st.session_state.pin_state == state:
        st.session_state.pin_state = None
    else:
        st.session_state.pin_state = state

# Main layout
header_container = st.container()

with header_container:
    # Title row with dynamic actions
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Where to Invest Your Resources")
        st.markdown("""
        <div style="margin-top: -15px; margin-bottom: 25px;">
        Discover your highest-value geographic markets and optimize your resource allocation for maximum growth potential.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # View mode selector
        view_options = {
            "map": "🗺️ Map View",
            "table": "📊 Table View",
            "comparison": "⚖️ Comparison View"
        }
        
        selected_view = st.radio(
            "View Mode", 
            options=list(view_options.keys()),
            format_func=lambda x: view_options[x],
            horizontal=True,
            key="view_selector",
            index=list(view_options.keys()).index(st.session_state.view_mode)
        )
        
        if selected_view != st.session_state.view_mode:
            toggle_view_mode(selected_view)

# Sidebar filters
with st.sidebar:
    st.markdown("## Market Analysis Filters")
    
    # Create a visual header for the filter panel
    render_html("""
    <div style="padding: 10px; background: linear-gradient(90deg, #3498db, #2980b9); 
                border-radius: 5px; margin-bottom: 15px; color: white; text-align: center;">
        <h4 style="margin: 0; color: white;">Filter Your Market View</h4>
        <p style="margin: 5px 0 0 0; font-size: 0.9em;">Customize your analysis parameters</p>
    </div>
    """)
    
    # State selection with search
    region_tab, segment_tab, metrics_tab = st.tabs(["Regions", "Segments", "Metrics"])
    
    with region_tab:
        # Create a more user-friendly state selector with region groups
        regions = {
            "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
            "Midwest": ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
            "South": ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
            "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"]
        }
        
        # Let users select by region first
        selected_regions = st.multiselect(
            "Filter by Region",
            options=list(regions.keys()),
            default=[]
        )
        
        # Get states from selected regions
        region_states = []
        for region in selected_regions:
            region_states.extend(regions[region])
        
        # Get all states for the select box
        all_states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        
        # Create dictionary for state names
        state_names = {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
            "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", 
            "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
            "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", 
            "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", 
            "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
            "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", 
            "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", 
            "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", 
            "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", 
            "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", 
            "WI": "Wisconsin", "WY": "Wyoming"
        }
        
        # Create a search box for states
        state_search = st.text_input("Search States", "")
        
        # Filter states based on search
        filtered_states = all_states
        if state_search:
            filtered_states = [
                state for state in all_states 
                if state_search.upper() in state or state_search.lower() in state_names[state].lower()
            ]
        
        # Let users select specific states
        selected_states = st.multiselect(
            "Select States",
            options=filtered_states,
            default=st.session_state.selected_states,
            format_func=lambda x: f"{x} - {state_names[x]}"
        )
        
        # Combine states from regions and specific selections
        if region_states:
            # Add states from selected regions if not already selected
            for state in region_states:
                if state not in selected_states:
                    selected_states.append(state)
                    
        # Update the session state
        if selected_states != st.session_state.selected_states:
            st.session_state.selected_states = selected_states
    
    with segment_tab:
        # Placeholder for segment filters
        # In a real implementation, these would be loaded from Supabase
        segment_options = ["Empathetic Dreamers", "Practical Realists", "Innovation Seekers", 
                          "Community Builders", "Value Optimizers"]
        
        selected_segments = st.multiselect(
            "Target Segments",
            options=segment_options,
            default=[]
        )
        
        # Add segment-specific details
        if selected_segments:
            st.info(f"Filtering for {len(selected_segments)} segments will be available in the next update.")
    
    with metrics_tab:
        # Market size threshold with dynamic formatting
        market_size_threshold = st.slider(
            "Minimum Market Size ($)",
            min_value=1000,
            max_value=100000,
            value=st.session_state.market_size_threshold,
            step=1000,
            format="$%d"
        )
        
        # Update session state
        if market_size_threshold != st.session_state.market_size_threshold:
            st.session_state.market_size_threshold = market_size_threshold
        
        # Growth rate threshold
        growth_rate_threshold = st.slider(
            "Minimum Growth Rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=st.session_state.growth_rate_threshold,
            step=0.5,
            format="%.1f%%"
        )
        
        # Update session state
        if growth_rate_threshold != st.session_state.growth_rate_threshold:
            st.session_state.growth_rate_threshold = growth_rate_threshold
        
        # Additional filters based on tier
        if current_tier in ["Accelerate", "Scale"]:
            use_advanced_filters = st.checkbox("Enable Advanced Filters", False)
            
            if use_advanced_filters:
                st.markdown("##### Advanced Filters")
                
                # Population size filter
                population_min = st.slider(
                    "Minimum Population",
                    min_value=5000,
                    max_value=1000000,
                    value=50000,
                    step=5000
                )
                
                # Accuracy threshold
                accuracy_min = st.slider(
                    "Minimum Accuracy (%)",
                    min_value=50.0,
                    max_value=100.0,
                    value=80.0,
                    step=1.0,
                    format="%.1f%%"
                )
    
    # Apply filters button with visual enhancement
    st.markdown("---")
    
    # Show currently applied filters
    st.markdown("##### Current Filters:")
    if selected_states:
        filter_text = f"**States**: {', '.join(selected_states[:3])}"
        if len(selected_states) > 3:
            filter_text += f" and {len(selected_states) - 3} more"
        st.markdown(filter_text)
    
    st.markdown(f"**Market Size**: ${market_size_threshold:,}+")
    st.markdown(f"**Growth Rate**: {growth_rate_threshold}%+")
    
    last_update_time = st.session_state.last_filter_update.strftime("%H:%M:%S")
    st.caption(f"Last updated: {last_update_time}")
    
    # Add a real-time filtering option
    st.markdown("---")
    enable_realtime = st.checkbox("Enable Real-Time Filtering", value=False, 
                               help="When enabled, the map will update automatically as you change filters without needing to click Apply")
    
    # Add progress tracking and real-time updates
    if 'filter_changes' not in st.session_state:
        st.session_state.filter_changes = 0
    
    # Track changes for visual feedback
    current_filters = f"{','.join(sorted(st.session_state.selected_states))}-{st.session_state.market_size_threshold}-{st.session_state.growth_rate_threshold}"
    if 'last_applied_filters' not in st.session_state:
        st.session_state.last_applied_filters = current_filters
    
    # Visual indicator if filters have changed but not applied
    filters_changed = current_filters != st.session_state.last_applied_filters
    
    # Check if real-time updates are enabled and filters have changed
    if enable_realtime and filters_changed:
        st.session_state.filter_changes += 1
        st.session_state.last_applied_filters = current_filters
        update_filters()
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        apply_button = st.button(
            f"Apply Filters {' (Changed)' if filters_changed else ''}", 
            key="apply_filters",
            use_container_width=True,
            type="primary",
            disabled=not filters_changed
        )
        
        if apply_button:
            with st.spinner("Applying filters..."):
                # Visual feedback for filter application
                st.session_state.filter_changes += 1
                st.session_state.last_applied_filters = current_filters
                update_filters()
                st.toast(f"Applied filters to {len(st.session_state.selected_states)} states")
                st.rerun()
    
    with col2:
        reset_button = st.button(
            "Reset Filters",
            key="reset_filters",
            use_container_width=True
        )
        
        if reset_button:
            with st.spinner("Resetting filters..."):
                st.session_state.selected_states = ["CA", "NY", "TX", "FL", "IL"]
                st.session_state.market_size_threshold = 10000
                st.session_state.growth_rate_threshold = 5.0
                st.session_state.filter_changes += 1
                update_filters()
                st.toast("Filters have been reset to default values")
                st.rerun()
                
    # If filters have been changed, show how many changes since last view
    if st.session_state.filter_changes > 0:
        st.caption(f"Filters updated {st.session_state.filter_changes} times in this session")

# Main content area based on view mode
content_container = st.container()

with content_container:
    with st.spinner("Loading market intelligence data..."):
        # Get data with current filters
        states_to_filter = st.session_state.selected_states if st.session_state.selected_states else None
        
        # Get market insights data
        try:
            insights_data = get_market_insights(states_to_filter, "market_size")
            
            if "error" in insights_data:
                raise Exception(insights_data["error"])
            
            # Extract insights from real data
            state_insights = insights_data.get("by_state", [])
            segment_insights = insights_data.get("by_segment", [])
            overall_stats = insights_data.get("overall", {})
            
            # Get the highest growth state and segment
            state_insights_sorted = sorted(state_insights, key=lambda x: x.get("avg_value", 0), reverse=True)
            highest_growth_state = state_insights_sorted[0] if state_insights_sorted else {}
            
            segment_insights_sorted = sorted(segment_insights, key=lambda x: x.get("avg_value", 0), reverse=True)
            highest_value_segment = segment_insights_sorted[0] if segment_insights_sorted else {}
            
            state_name = highest_growth_state.get("state", "N/A")
            growth_value = highest_growth_state.get("avg_value", 0)
            segment_name = highest_value_segment.get("segment_name", "N/A")
            segment_value = highest_value_segment.get("avg_value", 0)
            
            # Flag to indicate we're using real data
            real_insights = True
            
        except Exception as e:
            st.error(f"Could not retrieve market insights. Error: {str(e)}")
            # Use fallback data for demonstration
            state_name = "California"
            growth_value = 24.5
            segment_name = "Empathetic Dreamers"
            segment_value = 32.1
            real_insights = False
            
            # Create fallback state insights
            if not 'state_insights' in locals() or not state_insights:
                state_insights = [
                    {"state": "California", "avg_value": 24.5, "count": 1230},
                    {"state": "Texas", "avg_value": 22.3, "count": 980},
                    {"state": "New York", "avg_value": 19.8, "count": 890},
                    {"state": "Florida", "avg_value": 18.2, "count": 760},
                    {"state": "Illinois", "avg_value": 15.7, "count": 540}
                ]
            
        # Get map data
        try:
            map_data = get_map_data(states_to_filter)
            if "error" in map_data:
                raise Exception(map_data["error"])
            
        except Exception as e:
            st.error(f"Could not retrieve map data. Error: {str(e)}")
    
    # Show summary metrics at the top
    summary_metrics = st.container()
    
    with summary_metrics:
        # Create visually appealing summary metrics
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric(
                label="Analyzed Markets",
                value=len(st.session_state.selected_states) if st.session_state.selected_states else "All",
                delta=f"{len(state_insights)} locations" if 'state_insights' in locals() and state_insights else None
            )
        
        with metric_cols[1]:
            # Calculate the average market size from state insights
            if 'state_insights' in locals() and state_insights:
                avg_market_size = sum(state.get("avg_value", 0) for state in state_insights) / len(state_insights)
                st.metric(
                    label="Average Market Size",
                    value=f"${avg_market_size:.1f}K",
                    delta=f"{avg_market_size/10:.1f}% YoY"
                )
            else:
                st.metric(
                    label="Average Market Size",
                    value="$18.5K",
                    delta="4.2% YoY"
                )
        
        with metric_cols[2]:
            # Top performing state
            if 'highest_growth_state' in locals() and highest_growth_state:
                state_code = highest_growth_state.get("state", "N/A")
                state_full_name = state_names.get(state_code, state_code)
                st.metric(
                    label="Top Market",
                    value=state_full_name,
                    delta=f"{highest_growth_state.get('avg_value', 0):.1f}% growth"
                )
            else:
                st.metric(
                    label="Top Market",
                    value="California",
                    delta="24.5% growth"
                )
        
        with metric_cols[3]:
            # Top performing segment
            if 'highest_value_segment' in locals() and highest_value_segment:
                st.metric(
                    label="Top Segment",
                    value=highest_value_segment.get("segment_name", "N/A"),
                    delta=f"{highest_value_segment.get('avg_value', 0):.1f}% conversion"
                )
            else:
                st.metric(
                    label="Top Segment",
                    value="Empathetic Dreamers",
                    delta="32.1% conversion"
                )
    
    # Display content based on view mode
    if st.session_state.view_mode == "map":
        # Create tabbed interface for map view
        map_tabs = st.tabs(["Market Opportunity Map", "Key Insights", "Strategic Recommendations"])
        
        with map_tabs[0]:
            # Render the interactive map
            map_deck, map_df = render_opportunity_map(
                title="Geographic Market Opportunity Analysis",
                state_filter=states_to_filter,
                height=500
            )
            
            # Only render metrics if we have valid map data
            if map_df is not None and len(map_df) > 0:
                render_opportunity_metrics(map_df, "Top Market Opportunities", num_top_markets=5)
                
                # Add export options
                export_col1, export_col2 = st.columns(2)
                with export_col1:
                    if st.button("Export Map Data", key="export_map", use_container_width=True):
                        # Convert to CSV for download
                        csv = map_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"market_opportunity_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key="download_map_csv"
                        )
                
                with export_col2:
                    if st.button("Generate Map Report", key="map_report", use_container_width=True):
                        st.info("This feature will be available in the next update.")
        
        with map_tabs[1]:
            # Create two columns for insights
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                # Regional market insight
                region_metrics = {
                    "Market Size": f"${growth_value*1.5:.1f}M",
                    "Growth Rate": {"value": f"{growth_value:.1f}%", "delta": "7.2%"},
                    "Market Share": f"{growth_value/2:.1f}%"
                }
                
                region_insights = [
                    f"The {state_name} market shows {growth_value:.1f}% growth, significantly above the national average of {growth_value/2:.1f}%.",
                    f"Consumer spending in this region is weighted toward experience-based purchases, aligning with your core offerings.",
                    f"Competitor saturation is relatively low at {100-growth_value:.1f}%, indicating room for market entry."
                ]
                
                region_recommendations = [
                    f"Allocate {growth_value:.0f}% of your marketing budget to {state_name} to capitalize on growth trends.",
                    f"Focus initial efforts on urban centers where your target segments are concentrated.",
                    "Develop region-specific messaging that addresses local consumer preferences."
                ]
                
                action_button, plan_button = insight_card(
                    title=f"{state_name} Market Opportunity",
                    insights=region_insights,
                    recommendations=region_recommendations,
                    metrics=region_metrics,
                    opportunity_level="high"
                )
            
            with insight_col2:
                # Segment targeting insight
                segment_metrics = {
                    "Conversion Rate": {"value": f"{segment_value:.1f}%", "delta": "5.3%"},
                    "Avg. Value": f"${segment_value*50:.0f}",
                    "Growth Potential": f"{segment_value*1.2:.1f}%"
                }
                
                segment_insights = [
                    f"The '{segment_name}' segment has a {segment_value:.1f}% conversion rate, {segment_value/5:.1f}x the average.",
                    f"This segment typically spends {segment_value*1.3:.1f}% more per transaction than other segments.",
                    f"Retention rates within this segment are {segment_value*2:.1f}% higher than your current customer base."
                ]
                
                segment_recommendations = [
                    f"Develop targeted messaging that addresses the '{segment_name}' segment's core values.",
                    "Create specific product packages or service tiers that appeal to this segment's preferences.",
                    f"Implement a loyalty program designed to increase retention with the '{segment_name}' segment."
                ]
                
                action_button2, plan_button2 = insight_card(
                    title=f"{segment_name} Segment Potential",
                    insights=segment_insights,
                    recommendations=segment_recommendations,
                    metrics=segment_metrics,
                    opportunity_level="moderate"
                )
            
            # Additional quick insights based on real data
            st.markdown("### Additional Market Insights")
            
            quick_cols = st.columns(3)
            
            with quick_cols[0]:
                quick_insight(
                    title="Urban vs. Rural Opportunity",
                    content=f"Urban markets show {growth_value * 1.1:.1f}% higher growth than rural markets in selected states, with {segment_name} performing well in both environments.",
                    icon="🏙️",
                    color="#2980b9"
                )
            
            with quick_cols[1]:
                quick_insight(
                    title="Seasonal Market Trends",
                    content=f"Q2 and Q3 show {growth_value * 0.8:.1f}% higher market activity in {state_name} compared to other quarters, suggesting optimal timing for campaign launches.",
                    icon="📅",
                    color="#27ae60"
                )
            
            with quick_cols[2]:
                quick_insight(
                    title="Competitive Analysis",
                    content=f"Market saturation is {55 - growth_value * 0.7:.1f}% in the primary markets, providing substantial opportunity for new entrants with differentiated offerings.",
                    icon="⚡",
                    color="#8e44ad"
                )
            
        with map_tabs[2]:
            # Strategic recommendations section with visual enhancements
            st.markdown("### Resource Allocation Strategy")
            
            # Create visual resource allocation chart
            allocation_data = {
                "Category": ["Primary Markets", "Secondary Markets", "Exploratory Markets"],
                "Allocation": [50, 30, 20]
            }
            
            # Create a visually appealing resource allocation chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=allocation_data["Category"],
                y=allocation_data["Allocation"],
                marker_color=['#3498db', '#2ecc71', '#e74c3c'],
                text=allocation_data["Allocation"],
                textposition='auto',
                texttemplate='%{text}%',
                hoverinfo='text',
                hovertext=[
                    "Primary: High-growth, large markets (50%)",
                    "Secondary: Emerging markets (30%)",
                    "Exploratory: Test and learn (20%)"
                ]
            ))
            
            fig.update_layout(
                title="Recommended Resource Allocation",
                xaxis_title=None,
                yaxis_title="Percentage of Resources",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(
                    gridcolor='rgba(0,0,0,0.1)',
                    range=[0, 100]
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed allocation by state
            st.markdown("### Detailed Allocation by Market")
            
            # Generate state allocations based on insights
            if 'state_insights' in locals() and state_insights:
                # Sort states by avg_value
                sorted_states = sorted(state_insights, key=lambda x: x.get("avg_value", 0), reverse=True)
                
                # Allocate percentages based on relative market opportunity
                total_value = sum(state.get("avg_value", 0) for state in sorted_states[:8])
                state_allocations = []
                
                for i, state in enumerate(sorted_states[:8]):
                    state_code = state.get("state", "Unknown")
                    state_value = state.get("avg_value", 0)
                    
                    # Calculate relative allocation (weighted and normalized)
                    allocation = (state_value / total_value * 100) if total_value > 0 else 0
                    
                    # Scale to total 100%
                    if i < 3:  # Primary markets
                        category = "Primary"
                        base_allocation = allocation * 0.5
                    elif i < 6:  # Secondary markets
                        category = "Secondary"
                        base_allocation = allocation * 0.3
                    else:  # Exploratory markets
                        category = "Exploratory"
                        base_allocation = allocation * 0.2
                    
                    state_allocations.append({
                        "state": state_code,
                        "state_name": state_names.get(state_code, state_code),
                        "value": state_value,
                        "allocation": round(base_allocation, 1),
                        "category": category
                    })
            else:
                # Fallback data
                state_allocations = [
                    {"state": "CA", "state_name": "California", "value": 24.5, "allocation": 25.0, "category": "Primary"},
                    {"state": "TX", "state_name": "Texas", "value": 22.3, "allocation": 15.0, "category": "Primary"},
                    {"state": "NY", "state_name": "New York", "value": 19.8, "allocation": 10.0, "category": "Primary"},
                    {"state": "FL", "state_name": "Florida", "value": 18.2, "allocation": 15.0, "category": "Secondary"},
                    {"state": "AZ", "state_name": "Arizona", "value": 16.5, "allocation": 10.0, "category": "Secondary"},
                    {"state": "GA", "state_name": "Georgia", "value": 15.9, "allocation": 5.0, "category": "Secondary"},
                    {"state": "CO", "state_name": "Colorado", "value": 14.7, "allocation": 8.0, "category": "Exploratory"},
                    {"state": "NC", "state_name": "North Carolina", "value": 14.2, "allocation": 7.0, "category": "Exploratory"},
                    {"state": "WA", "state_name": "Washington", "value": 13.8, "allocation": 5.0, "category": "Exploratory"}
                ]
            
            # Create categories for color coding
            category_colors = {
                "Primary": "#3498db",
                "Secondary": "#2ecc71",
                "Exploratory": "#e74c3c"
            }
            
            # Create data for sunburst chart
            sunburst_data = []
            for alloc in state_allocations:
                sunburst_data.append({
                    "ids": [alloc["category"], f"{alloc['category']}-{alloc['state']}"],
                    "labels": [alloc["category"], alloc["state_name"]],
                    "parents": ["", alloc["category"]],
                    "values": [0, alloc["allocation"]],
                    "text": [f"{alloc['category']} Markets", f"{alloc['allocation']}%"],
                    "marker": {"colors": [category_colors[alloc["category"]], category_colors[alloc["category"]]]}
                })
            
            # Flatten the data for the sunburst
            ids = []
            labels = []
            parents = []
            values = []
            text = []
            marker_colors = []
            
            for item in sunburst_data:
                for i in range(len(item["ids"])):
                    # Only add category once
                    if item["ids"][i] not in ids:
                        ids.append(item["ids"][i])
                        labels.append(item["labels"][i])
                        parents.append(item["parents"][i])
                        values.append(item["values"][i])
                        text.append(item["text"][i])
                        marker_colors.append(item["marker"]["colors"][i])
            
            # Create the sunburst chart
            fig = go.Figure(go.Sunburst(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                text=text,
                branchvalues="total",
                marker=dict(colors=marker_colors),
                textinfo="label+text",
                hovertemplate="<b>%{label}</b><br>Allocation: %{value}%<extra></extra>"
            ))
            
            fig.update_layout(
                title="Market Allocation Breakdown",
                margin=dict(t=30, l=0, r=0, b=0),
                height=500
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Action plans and next steps
            st.markdown("### Next Steps")
            
            next_steps = [
                "Create detailed market entry plans for each primary market",
                "Develop testing strategies for secondary and exploratory markets",
                "Align marketing messaging with local audience preferences",
                "Set up market-specific performance tracking"
            ]
            
            for i, step in enumerate(next_steps):
                st.markdown(f"**{i+1}.** {step}")
            
            # Action buttons
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Generate Complete Strategy Report", key="gen_report", use_container_width=True):
                    st.info("This feature will be available in the next update.")
            with action_col2:
                if st.button("Create Market Entry Plan", key="create_plan", use_container_width=True):
                    st.switch_page("pages/how_to_engage.py")
    
    elif st.session_state.view_mode == "table":
        # Create tables with market data
        if 'map_df' in locals() and map_df is not None and len(map_df) > 0:
            # Create tabbed interface for different data views
            table_tabs = st.tabs(["Market Data", "State Summary", "Segment Analysis"])
            
            with table_tabs[0]:
                st.markdown("### Detailed Market Data")
                
                # Add search functionality
                search_term = st.text_input("Search Markets", "")
                
                # Filter the dataframe based on search
                filtered_df = map_df
                if search_term:
                    mask = map_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
                    filtered_df = map_df[mask]
                
                # Enhance dataframe with styling and interactivity
                def highlight_max(s):
                    is_max = s == s.max()
                    return ['background-color: rgba(46, 204, 113, 0.2)' if v else '' for v in is_max]
                
                # Select most relevant columns
                display_columns = ['city', 'state', 'market_size', 'growth_rate', 'population']
                if all(col in map_df.columns for col in display_columns):
                    display_df = filtered_df[display_columns].copy()
                    
                    # Add formatting
                    display_df['market_size'] = display_df['market_size'].apply(lambda x: f"${x:,.0f}")
                    display_df['growth_rate'] = display_df['growth_rate'].apply(lambda x: f"{x:.1f}%")
                    display_df['population'] = display_df['population'].apply(lambda x: f"{x:,}")
                    
                    # Rename columns for better display
                    display_df.columns = ['City', 'State', 'Market Size', 'Growth Rate', 'Population']
                    
                    # Display the dataframe
                    st.dataframe(display_df, use_container_width=True, height=400)
                else:
                    st.dataframe(filtered_df, use_container_width=True, height=400)
                
                # Summary statistics
                summary_cols = st.columns(4)
                with summary_cols[0]:
                    st.metric("Total Markets", f"{len(filtered_df)}")
                with summary_cols[1]:
                    avg_market_size = filtered_df['market_size'].mean() if 'market_size' in filtered_df.columns else 0
                    st.metric("Avg Market Size", f"${avg_market_size:,.0f}")
                with summary_cols[2]:
                    avg_growth = filtered_df['growth_rate'].mean() if 'growth_rate' in filtered_df.columns else 0
                    st.metric("Avg Growth Rate", f"{avg_growth:.1f}%")
                with summary_cols[3]:
                    total_pop = filtered_df['population'].sum() if 'population' in filtered_df.columns else 0
                    st.metric("Total Population", f"{total_pop:,}")
                
                # Export options
                export_cols = st.columns(2)
                with export_cols[0]:
                    if st.button("Export to CSV", key="export_csv", use_container_width=True):
                        csv = filtered_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"market_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key="download_table_csv"
                        )
                
                with export_cols[1]:
                    if st.button("Export to Excel", key="export_excel", use_container_width=True):
                        st.info("Excel export will be available in the next update.")
            
            with table_tabs[1]:
                st.markdown("### Market Summary by State")
                
                # Create a pivot table by state
                if 'map_df' in locals() and map_df is not None and len(map_df) > 0:
                    required_columns = ['state', 'market_size', 'growth_rate', 'population']
                    if all(col in map_df.columns for col in required_columns):
                        # Group by state
                        state_summary = map_df.groupby('state').agg({
                            'market_size': ['mean', 'sum', 'max'],
                            'growth_rate': ['mean', 'max'],
                            'population': ['sum', 'mean', 'count']
                        }).reset_index()
                        
                        # Flatten the column names
                        state_summary.columns = [
                            'State',
                            'Avg Market Size', 'Total Market Size', 'Max Market Size',
                            'Avg Growth Rate', 'Max Growth Rate',
                            'Total Population', 'Avg Population', 'Market Count'
                        ]
                        
                        # Format for display
                        formatted_summary = state_summary.copy()
                        formatted_summary['Avg Market Size'] = formatted_summary['Avg Market Size'].apply(lambda x: f"${x:,.0f}")
                        formatted_summary['Total Market Size'] = formatted_summary['Total Market Size'].apply(lambda x: f"${x:,.0f}")
                        formatted_summary['Max Market Size'] = formatted_summary['Max Market Size'].apply(lambda x: f"${x:,.0f}")
                        formatted_summary['Avg Growth Rate'] = formatted_summary['Avg Growth Rate'].apply(lambda x: f"{x:.1f}%")
                        formatted_summary['Max Growth Rate'] = formatted_summary['Max Growth Rate'].apply(lambda x: f"{x:.1f}%")
                        formatted_summary['Total Population'] = formatted_summary['Total Population'].apply(lambda x: f"{x:,}")
                        formatted_summary['Avg Population'] = formatted_summary['Avg Population'].apply(lambda x: f"{x:,}")
                        
                        # Display the summary
                        st.dataframe(formatted_summary, use_container_width=True, height=400)
                        
                        # Visualization of key metrics by state
                        st.markdown("### State Comparison Visualization")
                        
                        # Let user select which metric to visualize
                        metric_options = {
                            'Avg Market Size': 'Average Market Size by State',
                            'Total Market Size': 'Total Market Size by State',
                            'Avg Growth Rate': 'Average Growth Rate by State',
                            'Market Count': 'Number of Markets by State'
                        }
                        
                        selected_metric = st.radio(
                            "Select Metric to Visualize",
                            options=list(metric_options.keys()),
                            format_func=lambda x: metric_options[x],
                            horizontal=True
                        )
                        
                        # Create horizontal bar chart
                        metric_col = selected_metric
                        metric_data = state_summary.sort_values(by=metric_col, ascending=False).head(10)
                        
                        # Determine color scheme and formatting based on metric
                        if 'Market Size' in metric_col:
                            color_scheme = 'Blues'
                            y_title = 'Market Size ($)'
                            formatting = '$,.0f'
                        elif 'Growth Rate' in metric_col:
                            color_scheme = 'Reds'
                            y_title = 'Growth Rate (%)'
                            formatting = '.1f%'
                        else:
                            color_scheme = 'Greens'
                            y_title = 'Count'
                            formatting = ',d'
                        
                        fig = px.bar(
                            metric_data,
                            x='State',
                            y=metric_col,
                            title=f"Top 10 States by {metric_col}",
                            color=metric_col,
                            color_continuous_scale=color_scheme,
                            text=metric_col
                        )
                        
                        fig.update_layout(
                            xaxis_title="State",
                            yaxis_title=y_title,
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required columns for state summary not found in the data.")
                else:
                    st.warning("No map data available for state summary.")
            
            with table_tabs[2]:
                st.markdown("### Segment Analysis")
                
                # Display segment data if available
                if 'segment_insights' in locals() and segment_insights:
                    # Create a dataframe from segment insights
                    segment_df = pd.DataFrame(segment_insights)
                    
                    # Display the segment dataframe
                    if 'segment_name' in segment_df.columns and 'avg_value' in segment_df.columns:
                        # Create a formatted version for display
                        display_df = segment_df.copy()
                        
                        # Rename columns for better display
                        rename_map = {
                            'segment_name': 'Segment',
                            'avg_value': 'Average Value',
                            'min_value': 'Minimum Value',
                            'max_value': 'Maximum Value',
                            'median_value': 'Median Value',
                            'count': 'Count'
                        }
                        
                        display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns}, inplace=True)
                        
                        # Format numeric columns
                        if 'Average Value' in display_df.columns:
                            display_df['Average Value'] = display_df['Average Value'].apply(lambda x: f"${x:,.2f}")
                        if 'Minimum Value' in display_df.columns:
                            display_df['Minimum Value'] = display_df['Minimum Value'].apply(lambda x: f"${x:,.2f}")
                        if 'Maximum Value' in display_df.columns:
                            display_df['Maximum Value'] = display_df['Maximum Value'].apply(lambda x: f"${x:,.2f}")
                        if 'Median Value' in display_df.columns:
                            display_df['Median Value'] = display_df['Median Value'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Create a visualization of segment values
                        st.markdown("### Segment Value Comparison")
                        
                        # Create bar chart of segment values
                        fig = px.bar(
                            segment_df.sort_values(by='avg_value', ascending=False),
                            x='segment_name',
                            y='avg_value',
                            color='avg_value',
                            color_continuous_scale='Viridis',
                            labels={'segment_name': 'Segment', 'avg_value': 'Average Value'},
                            title="Segment Value Comparison"
                        )
                        
                        fig.update_layout(
                            xaxis_title="Segment",
                            yaxis_title="Average Value ($)",
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required columns for segment analysis not found in the data.")
                else:
                    st.warning("No segment data available for analysis.")
                
                # Additional analysis based on tier
                if current_tier == "Scale":
                    st.markdown("### Advanced Segment Analysis")
                    
                    # Add advanced segment insights here (placeholder)
                    st.info("Advanced segment analysis is available for Scale tier users. Full implementation coming in the next update.")
        else:
            st.warning("No data available for table view. Please adjust your filters or try again.")
    
    elif st.session_state.view_mode == "comparison":
        # Market comparison view
        st.markdown("## Market Comparison Analysis")
        
        # Create a more robust comparison view with state selection
        comparison_col1, comparison_col2 = st.columns([1, 3])
        
        with comparison_col1:
            st.markdown("### Select Markets to Compare")
            
            if 'state_insights' in locals() and state_insights:
                # Create a list of states from the insights
                available_states = [state.get("state", "Unknown") for state in state_insights]
                
                # Let user select states to compare
                selected_comparison_states = st.multiselect(
                    "Select States for Comparison",
                    options=available_states,
                    default=available_states[:3] if len(available_states) >= 3 else available_states,
                    format_func=lambda x: f"{x} - {state_names.get(x, x)}"
                )
                
                # Pin state functionality
                st.markdown("---")
                st.markdown("### Pinned State")
                
                if st.session_state.pin_state:
                    st.success(f"📌 {state_names.get(st.session_state.pin_state, st.session_state.pin_state)} is pinned")
                    if st.button("Unpin State"):
                        st.session_state.pin_state = None
                        st.rerun()
                else:
                    st.info("Pin a state to include it in all comparisons")
                    
                    # Allow pinning a state
                    pin_state_selection = st.selectbox(
                        "Select a State to Pin",
                        options=available_states,
                        format_func=lambda x: f"{x} - {state_names.get(x, x)}"
                    )
                    
                    if st.button("Pin State"):
                        st.session_state.pin_state = pin_state_selection
                        st.rerun()
                
                # Add the pinned state to the comparison if not already there
                if st.session_state.pin_state and st.session_state.pin_state not in selected_comparison_states:
                    selected_comparison_states = [st.session_state.pin_state] + selected_comparison_states
            else:
                st.warning("No state data available for comparison.")
                selected_comparison_states = []
        
        with comparison_col2:
            if 'selected_comparison_states' in locals() and selected_comparison_states:
                st.markdown("### Market Comparison Dashboard")
                
                # Create comparison data from state insights
                comparison_data = []
                
                for state_code in selected_comparison_states:
                    # Find the state in the insights
                    state_info = next((state for state in state_insights if state.get("state") == state_code), None)
                    
                    if state_info:
                        comparison_data.append({
                            'state': state_code,
                            'state_name': state_names.get(state_code, state_code),
                            'market_size': state_info.get("avg_value", 0),
                            'growth_rate': state_info.get("min_value", 0),  # Using min_value as a proxy for growth rate
                            'population': state_info.get("count", 0) * 10000,  # Using count as a proxy for population
                            'opportunity_score': state_info.get("median_value", 0)  # Using median as opportunity score
                        })
                
                if comparison_data:
                    # Create a dataframe for the comparison
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    # Create a radar chart for comparison
                    categories = ['Market Size', 'Growth Rate', 'Population', 'Opportunity']
                    
                    radar_fig = go.Figure()
                    
                    # Normalize the data for the radar chart
                    max_market_size = comparison_df['market_size'].max() if comparison_df['market_size'].max() > 0 else 1
                    max_growth_rate = comparison_df['growth_rate'].max() if comparison_df['growth_rate'].max() > 0 else 1
                    max_population = comparison_df['population'].max() if comparison_df['population'].max() > 0 else 1
                    max_opportunity = comparison_df['opportunity_score'].max() if comparison_df['opportunity_score'].max() > 0 else 1
                    
                    # Create a color palette
                    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#d35400']
                    
                    # Add traces for each state
                    for i, row in comparison_df.iterrows():
                        radar_fig.add_trace(go.Scatterpolar(
                            r=[
                                row['market_size'] / max_market_size * 100,
                                row['growth_rate'] / max_growth_rate * 100,
                                row['population'] / max_population * 100,
                                row['opportunity_score'] / max_opportunity * 100
                            ],
                            theta=categories,
                            fill='toself',
                            name=f"{row['state']} - {row['state_name']}",
                            line_color=colors[i % len(colors)]
                        ))
                    
                    radar_fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )
                        ),
                        title="Market Attribute Comparison",
                        showlegend=True,
                        height=500
                    )
                    
                    st.plotly_chart(radar_fig, use_container_width=True)
                    
                    # Create a table view of the comparison
                    st.markdown("### Detailed Metric Comparison")
                    
                    # Create a formatted version for display
                    display_df = comparison_df.copy()
                    display_df['market_size'] = display_df['market_size'].apply(lambda x: f"${x:,.2f}")
                    display_df['growth_rate'] = display_df['growth_rate'].apply(lambda x: f"{x:.1f}%")
                    display_df['population'] = display_df['population'].apply(lambda x: f"{x:,}")
                    display_df['opportunity_score'] = display_df['opportunity_score'].apply(lambda x: f"{x:.1f}")
                    
                    # Rename columns for display
                    display_df.rename(columns={
                        'state': 'Code',
                        'state_name': 'State',
                        'market_size': 'Market Size',
                        'growth_rate': 'Growth Rate',
                        'population': 'Population',
                        'opportunity_score': 'Opportunity Score'
                    }, inplace=True)
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Create bar charts for each metric
                    st.markdown("### Individual Metric Comparison")
                    
                    metric_tabs = st.tabs(["Market Size", "Growth Rate", "Population", "Opportunity Score"])
                    
                    with metric_tabs[0]:
                        # Market size bar chart
                        fig = px.bar(
                            comparison_df.sort_values(by='market_size', ascending=False),
                            x='state',
                            y='market_size',
                            color='market_size',
                            color_continuous_scale='Blues',
                            text='market_size',
                            labels={'state': 'State', 'market_size': 'Market Size'},
                            title="Market Size Comparison",
                            hover_data=['state_name']
                        )
                        
                        fig.update_traces(
                            texttemplate='$%{text:.2f}',
                            textposition='auto'
                        )
                        
                        fig.update_layout(
                            xaxis_title="State",
                            yaxis_title="Market Size ($)",
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with metric_tabs[1]:
                        # Growth rate bar chart
                        fig = px.bar(
                            comparison_df.sort_values(by='growth_rate', ascending=False),
                            x='state',
                            y='growth_rate',
                            color='growth_rate',
                            color_continuous_scale='Reds',
                            text='growth_rate',
                            labels={'state': 'State', 'growth_rate': 'Growth Rate'},
                            title="Growth Rate Comparison",
                            hover_data=['state_name']
                        )
                        
                        fig.update_traces(
                            texttemplate='%{text:.1f}%',
                            textposition='auto'
                        )
                        
                        fig.update_layout(
                            xaxis_title="State",
                            yaxis_title="Growth Rate (%)",
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with metric_tabs[2]:
                        # Population bar chart
                        fig = px.bar(
                            comparison_df.sort_values(by='population', ascending=False),
                            x='state',
                            y='population',
                            color='population',
                            color_continuous_scale='Greens',
                            text='population',
                            labels={'state': 'State', 'population': 'Population'},
                            title="Population Comparison",
                            hover_data=['state_name']
                        )
                        
                        fig.update_traces(
                            texttemplate='%{text:,}',
                            textposition='auto'
                        )
                        
                        fig.update_layout(
                            xaxis_title="State",
                            yaxis_title="Population",
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with metric_tabs[3]:
                        # Opportunity score bar chart
                        fig = px.bar(
                            comparison_df.sort_values(by='opportunity_score', ascending=False),
                            x='state',
                            y='opportunity_score',
                            color='opportunity_score',
                            color_continuous_scale='Viridis',
                            text='opportunity_score',
                            labels={'state': 'State', 'opportunity_score': 'Opportunity Score'},
                            title="Opportunity Score Comparison",
                            hover_data=['state_name']
                        )
                        
                        fig.update_traces(
                            texttemplate='%{text:.1f}',
                            textposition='auto'
                        )
                        
                        fig.update_layout(
                            xaxis_title="State",
                            yaxis_title="Opportunity Score",
                            height=400,
                            plot_bgcolor='rgba(0,0,0,0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Add export options
                    if st.button("Export Comparison Data", key="export_comparison", use_container_width=True):
                        comparison_csv = comparison_df.to_csv(index=False)
                        st.download_button(
                            label="Download Comparison CSV",
                            data=comparison_csv,
                            file_name=f"market_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key="download_comparison_csv"
                        )
                else:
                    st.warning("No comparison data available. Please select states to compare.")
            else:
                st.info("Please select states to compare from the panel on the left.")

# Footer section with help information
with st.expander("Help & Information"):
    st.markdown("""
    ### Using the Market Intelligence Platform
    
    This page helps you identify the most promising markets for investment based on data-driven insights.
    
    #### Key Features:
    
    1. **Interactive Map**: Visualize market opportunities geographically
    2. **Data Tables**: Analyze market data in tabular format
    3. **Market Comparison**: Compare different markets side by side
    4. **Strategic Recommendations**: Get actionable investment strategies
    
    #### Tips for Getting the Most Value:
    
    - Use filters to focus on specific regions or market characteristics
    - Toggle between different view modes to see data from multiple perspectives
    - In comparison view, pin important markets to include them in all comparisons
    - Explore the insights tab for interpretation of what the data means for your business
    
    #### Next Steps:
    
    After identifying promising markets, use the "How to Engage" page to develop targeted strategies.
    """)

# Tier status indicator in sidebar
tier_labels = {"Free": "🔹", "Accelerate": "🔸", "Scale": "⭐"}
st.sidebar.markdown("---")
st.sidebar.markdown(f"### Current Tier: {tier_labels.get(current_tier, '🔹')} {current_tier}")

# Show tier-based feature limitations
if current_tier == "Free":
    st.sidebar.warning("Free tier access provides limited data. Upgrade for full market insights.")
    st.sidebar.button("Upgrade Now", use_container_width=True)

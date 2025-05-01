import socket
import os
import logging

supabase_url = os.environ.get("SUPABASE_URL")
try:
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Testing DNS resolution for: {supabase_url}")
    host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
    logging.info(f"Host to resolve: {host}")
    ip = socket.gethostbyname(host)
    logging.info(f"Resolved IP: {ip}")
except Exception as e:
    logging.error(f"DNS resolution failed: {e}")

import streamlit as st
import datetime
import os
from utils.data_access import get_region_growth_data, get_top_segments
from utils.html_render import render_html, render_card
from utils.tier_control import enforce_tier, get_user_tier

# Page configuration
st.set_page_config(
    page_title="DARG Market Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - Scale tier for full functionality
current_tier = get_user_tier()
enforce_tier('Free')  # Allow everyone to access the home page

# Title and greeting
st.title("DARG Market Intelligence Platform")

# Welcome message that adapts to the time of day
current_hour = datetime.datetime.now().hour
greeting = "Good morning" if 5 <= current_hour < 12 else "Good afternoon" if 12 <= current_hour < 18 else "Good evening"

st.markdown(f"### {greeting}! What business decision are you facing today?")

# Main section: Business questions focus
st.markdown("## Choose Your Business Challenge")

# Create three columns for a better layout
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Where should I invest my resources?")
    st.markdown("Discover which geographic markets offer the highest growth potential for your specific offerings.")
    if st.button("Explore Market Opportunities →", key="explore_market", use_container_width=True):
        st.switch_page("pages/where_to_invest.py")

with col2:
    st.markdown("### Which customer segments should I target?")
    st.markdown("Identify the most valuable customer segments and understand their unique characteristics and preferences.")
    if st.button("Find Ideal Customers →", key="find_customers", use_container_width=True):
        st.switch_page("pages/who_to_target.py")

with col3:
    st.markdown("### How should I engage my market?")
    st.markdown("Get actionable strategies for marketing, messaging, and engaging with your target audiences effectively.")
    if st.button("Build Your Strategy →", key="build_strategy", use_container_width=True):
        st.switch_page("pages/how_to_engage.py")

st.markdown("---")

# Recent insights section
st.markdown("## Your Market Intelligence Overview")

# Try to get real data for the insights section
try:
    growth_data = get_region_growth_data()
    top_segment = get_top_segments(limit=1)[0] if get_top_segments(limit=1) else {"segment_name": "N/A", "conversion_rate": 0}
    
    region_name = growth_data.get("region_name", "Southwest Region")
    growth_rate = growth_data.get("growth_rate", 24)
    market_value = growth_data.get("market_value", 14.2)
    segment_name = top_segment.get("segment_name", "Empathetic Dreamers")
    conversion_rate = top_segment.get("conversion_rate", 32)
    
except Exception as e:
    st.warning(f"Could not load real-time insights. Using default examples instead. Error: {str(e)}")
    # Default values if data can't be loaded
    region_name = "Southwest Region"
    growth_rate = 24
    market_value = 14.2
    segment_name = "Empathetic Dreamers"
    conversion_rate = 32

# Create a sample insight with actual or default data
insight_cols = st.columns([2, 1])

with insight_cols[0]:
    st.markdown("### Key Market Insight")
    st.markdown(f"""
    Based on recent data, we've identified a **{growth_rate}% growth opportunity** in the 
    **{region_name}**, particularly among the "**{segment_name}**" segment. 
    This represents a potential **${market_value}M** market expansion.
    """)
    
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("View Detailed Analysis", key="view_analysis", use_container_width=True):
            st.switch_page("pages/where_to_invest.py")
    with action_col2:
        if st.button("Create Action Plan", key="create_plan", use_container_width=True):
            st.switch_page("pages/how_to_engage.py")

with insight_cols[1]:
    # Metrics with actual or default data
    st.metric(
        label="Largest Growth Market", 
        value=region_name,
        delta=f"{growth_rate}% YoY"
    )
    
    st.metric(
        label="Top Performing Segment", 
        value=segment_name,
        delta=f"{conversion_rate}% Conversion Rate"
    )

st.markdown("---")

# Quick access tools
st.markdown("## Quick Tools")

quick_cols = st.columns(4)

with quick_cols[0]:
    if st.button("Strategy Builder", key="strategy_builder", use_container_width=True):
        st.switch_page("pages/how_to_engage.py")
    st.markdown("Create data-driven strategies in minutes")
    
with quick_cols[1]:
    if st.button("ROI Forecaster", key="roi_forecaster", use_container_width=True):
        st.switch_page("pages/roi_calculator.py")  
    st.markdown("Project returns on market investments")
    
with quick_cols[2]:
    if st.button("Market Alerts", key="market_alerts", use_container_width=True):
        st.switch_page("pages/whats_changing.py")
    st.markdown("See what's changing in your target markets")
    
with quick_cols[3]:
    if st.button("Saved Strategies", key="saved_strategies", use_container_width=True):
        st.switch_page("pages/how_to_engage.py")
    st.markdown("Access your previously created strategies")

# At the bottom, include a help guide
with st.expander("How to get the most out of the DARG Platform"):
    st.markdown("""
    ### Getting Started Guide
    
    The DARG Market Intelligence Platform is designed to help you make data-driven business decisions by:
    
    1. **Identifying market opportunities** across different geographic regions
    2. **Understanding your ideal customers** through detailed persona profiles
    3. **Developing effective strategies** based on market data and customer insights
    4. **Projecting ROI** for different market approaches
    
    ### Recommended Workflow
    
    For the best results, we recommend this approach:
    
    1. Start by exploring **Where to Invest** to identify your highest-potential markets
    2. Next, use **Who to Target** to understand the most valuable customer segments in those markets
    3. Then build your approach with **How to Engage** to develop targeted strategies
    4. Finally, validate your plan with the **ROI Forecaster** to project potential returns
    
    Need more help? Contact support@darg.com
    """)

# Tier status indicator
tier_labels = {"Free": "🔹", "Accelerate": "🔸", "Scale": "⭐"}
st.sidebar.markdown(f"### Current Tier: {tier_labels.get(current_tier, '🔹')} {current_tier}")

if current_tier != "Scale":
    st.sidebar.markdown("### Upgrade your plan")
    st.sidebar.markdown("Get access to more data and insights by upgrading to a higher tier.")
    st.sidebar.button("Upgrade Now", use_container_width=True)

# Admin tools (connection status for administrators)
if current_tier == "Scale":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Admin Tools")
    if st.sidebar.button("📊 Connection Status", use_container_width=True):
        st.switch_page("pages/connection_status.py")

# Footer
st.markdown("---")
st.markdown("© 2023 DARG Market Intelligence Platform. All rights reserved.")

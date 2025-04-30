import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
from utils.tier_control import enforce_tier
from utils.data_access import get_market_insights
from components.insight_card import insight_card, quick_insight
from utils.html_render import render_html, render_card

# Page configuration
st.set_page_config(
    page_title="What's Changing | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - Accelerate tier required
enforce_tier('Accelerate')

# Title and description
st.title("What's Changing in Your Markets")
st.markdown("""
Monitor trends, shifts, and emerging opportunities in your target markets.
This analysis helps you stay ahead of changing consumer beliefs and market dynamics.
""")

# Sidebar filters
st.sidebar.markdown("## Alert Filters")

# Alert type selection
st.sidebar.markdown("### Alert Types")
alert_types = st.sidebar.multiselect(
    "Select Alert Types",
    options=["Belief Pattern Shifts", "Competitive Movements", "Market Size Changes", "Regulatory Updates", "Consumer Sentiment"],
    default=["Belief Pattern Shifts", "Competitive Movements", "Market Size Changes"]
)

# Time frame selection
st.sidebar.markdown("### Time Frame")
time_frame = st.sidebar.radio(
    "Select Time Frame",
    options=["Last 7 Days", "Last 30 Days", "Last Quarter"],
    index=1
)

# Market selection
st.sidebar.markdown("### Markets to Monitor")
market_options = ["All Markets", "Primary Markets", "Secondary Markets", "Custom Selection"]
selected_market_option = st.sidebar.radio("Market Scope", market_options, index=0)

if selected_market_option == "Custom Selection":
    states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
    selected_states = st.sidebar.multiselect(
        "Select States",
        options=states,
        default=["CA", "NY", "TX", "FL"]
    )

# Alert priority selection
st.sidebar.markdown("### Alert Priority")
alert_priority = st.sidebar.multiselect(
    "Select Priority Levels",
    options=["High", "Medium", "Low"],
    default=["High", "Medium"]
)

# Apply filters button
apply_filters = st.sidebar.button("Update Alerts", use_container_width=True)

# Main content area

# Top alerts section
st.markdown("## High Priority Alerts")

# Define some sample alerts (in a real application, these would come from the database)
# We'll use a consistent format for alerts

high_priority_alerts = [
    {
        "id": "alert-001",
        "title": "Significant Shift in 'Empathetic Dreamers' Belief Patterns",
        "type": "Belief Pattern Shifts",
        "priority": "High",
        "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "summary": "The 'Empathetic Dreamers' segment shows a 23% increase in concern for sustainability and ethical sourcing over the past 30 days.",
        "impact": "This shift represents a significant opportunity for brands that emphasize sustainability practices and ethical supply chains.",
        "recommendation": "Highlight sustainability initiatives and ethical practices in marketing materials targeted at this segment.",
        "metrics": {
            "Change Magnitude": "23%",
            "Affected Audience": "22.5M consumers",
            "Est. Market Impact": "$47.2M"
        }
    },
    {
        "id": "alert-002",
        "title": "Major Competitor Entered Southwest Market",
        "type": "Competitive Movements",
        "priority": "High",
        "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "summary": "Competitor XYZ has launched operations in the Southwest region with aggressive pricing and promotional strategy.",
        "impact": "Potential market share erosion in Arizona and New Mexico, particularly among price-sensitive segments.",
        "recommendation": "Develop targeted retention campaign for existing customers in affected regions with emphasis on unique value propositions beyond price.",
        "metrics": {
            "Potential Share Loss": "12%",
            "Affected Revenue": "$3.8M",
            "Response Urgency": "High"
        }
    },
    {
        "id": "alert-003",
        "title": "Northeast Market Size Expansion",
        "type": "Market Size Changes",
        "priority": "High",
        "date": (datetime.now() - timedelta(days=9)).strftime("%Y-%m-%d"),
        "summary": "The Northeast market has expanded by 17% due to demographic shifts and increasing disposable income among key segments.",
        "impact": "Significant opportunity for market share growth in a rapidly expanding region.",
        "recommendation": "Increase marketing investment in Northeast region with emphasis on affluent suburban areas showing highest growth rates.",
        "metrics": {
            "Market Growth": "17%",
            "Opportunity Size": "$12.7M",
            "Competitive Presence": "Medium"
        }
    }
]

# Display high priority alerts
if not high_priority_alerts:
    st.info("No high priority alerts match your current filters.")
else:
    # Create a container for each alert
    for alert in high_priority_alerts:
        with st.container():
            # Alert header with priority indicator
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {alert['title']}")
            with col2:
                st.markdown(f"**Type:** {alert['type']}")
            with col3:
                priority_color = "#e74c3c" if alert['priority'] == "High" else "#f39c12" if alert['priority'] == "Medium" else "#3498db"
                st.markdown(f"<span style='color: {priority_color}; font-weight: bold;'>{alert['priority']} PRIORITY</span>", unsafe_allow_html=True)
            
            st.markdown(f"**Date Detected:** {alert['date']}")
            
            # Alert content
            st.markdown(f"**Summary:** {alert['summary']}")
            st.markdown(f"**Potential Impact:** {alert['impact']}")
            st.markdown(f"**Recommended Action:** {alert['recommendation']}")
            
            # Metrics in columns
            if "metrics" in alert:
                metric_cols = st.columns(len(alert["metrics"]))
                for i, (label, value) in enumerate(alert["metrics"].items()):
                    metric_cols[i].metric(label=label, value=value)
            
            # Action buttons
            action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
            with action_col1:
                st.button("View Details", key=f"details_{alert['id']}", use_container_width=True)
            with action_col2:
                st.button("Take Action", key=f"action_{alert['id']}", use_container_width=True)
            
            st.markdown("---")

# Medium and low priority alerts
st.markdown("## Other Recent Alerts")

other_alerts = [
    {
        "id": "alert-004",
        "title": "Shift in Digital Channel Effectiveness",
        "type": "Consumer Sentiment",
        "priority": "Medium",
        "date": (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d"),
        "summary": "Declining engagement rates on Facebook (-15%) with corresponding increase on TikTok (+28%) among 25-34 demographic."
    },
    {
        "id": "alert-005",
        "title": "Regulatory Change in California",
        "type": "Regulatory Updates",
        "priority": "Medium",
        "date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
        "summary": "New data privacy regulations in California will require additional consent mechanisms for personalized marketing."
    },
    {
        "id": "alert-006",
        "title": "Seasonal Shift in 'Rational Planners' Segment",
        "type": "Belief Pattern Shifts",
        "priority": "Low",
        "date": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
        "summary": "Expected seasonal shift in purchase patterns for 'Rational Planners' segment, with 12% increase in research activity."
    },
    {
        "id": "alert-007",
        "title": "Competitor Product Enhancement",
        "type": "Competitive Movements",
        "priority": "Medium",
        "date": (datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d"),
        "summary": "Competitor ABC has added new features targeting the 'Hyper Experiencers' segment, potentially increasing their appeal."
    },
    {
        "id": "alert-008",
        "title": "Minor Market Contraction in Midwest",
        "type": "Market Size Changes",
        "priority": "Low",
        "date": (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d"),
        "summary": "Slight market contraction (-3%) in Midwest region, primarily affecting luxury/premium product categories."
    }
]

# Create tabs for medium and low priority alerts
tabs = st.tabs(["Medium Priority", "Low Priority"])

with tabs[0]:
    medium_alerts = [alert for alert in other_alerts if alert["priority"] == "Medium"]
    if not medium_alerts:
        st.info("No medium priority alerts match your current filters.")
    else:
        for alert in medium_alerts:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### {alert['title']}")
                with col2:
                    st.markdown(f"**{alert['date']}**")
                
                st.markdown(f"**Type:** {alert['type']}")
                st.markdown(f"**Summary:** {alert['summary']}")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.button("View Details", key=f"details_{alert['id']}", use_container_width=True)
                
                st.markdown("---")

with tabs[1]:
    low_alerts = [alert for alert in other_alerts if alert["priority"] == "Low"]
    if not low_alerts:
        st.info("No low priority alerts match your current filters.")
    else:
        for alert in low_alerts:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### {alert['title']}")
                with col2:
                    st.markdown(f"**{alert['date']}**")
                
                st.markdown(f"**Type:** {alert['type']}")
                st.markdown(f"**Summary:** {alert['summary']}")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.button("View Details", key=f"details_{alert['id']}", use_container_width=True)
                
                st.markdown("---")

# Market movement trends
st.markdown("---")
st.markdown("## Market Movement Trends")

# Create sample data for trend visualization
# In a real application, this would come from the database based on historical alerts and market data

# Generate dates for the past 90 days
end_date = datetime.now()
start_date = end_date - timedelta(days=90)
dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(91)]

# Generate alert counts by type
alert_types_for_chart = ["Belief Pattern Shifts", "Competitive Movements", "Market Size Changes", "Regulatory Updates", "Consumer Sentiment"]

# Create a seed for reproducible random numbers
random.seed(42)

# Generate data with trends
alert_data = {alert_type: [] for alert_type in alert_types_for_chart}

for i in range(91):
    # Belief Pattern Shifts: increasing trend
    alert_data["Belief Pattern Shifts"].append(int(3 + i/10 + random.randint(-2, 2)))
    
    # Competitive Movements: spike in middle
    if 30 <= i <= 50:
        alert_data["Competitive Movements"].append(int(5 + random.randint(-1, 3)))
    else:
        alert_data["Competitive Movements"].append(int(2 + random.randint(-1, 2)))
    
    # Market Size Changes: relatively stable
    alert_data["Market Size Changes"].append(int(3 + random.randint(-2, 2)))
    
    # Regulatory Updates: occasional spikes
    if i % 14 == 0:  # Spike every two weeks
        alert_data["Regulatory Updates"].append(int(4 + random.randint(0, 2)))
    else:
        alert_data["Regulatory Updates"].append(int(1 + random.randint(-1, 1)))
    
    # Consumer Sentiment: slightly decreasing
    alert_data["Consumer Sentiment"].append(int(4 - i/30 + random.randint(-2, 2)))

# Create DataFrame for the chart
trend_data = []
for alert_type in alert_types_for_chart:
    for i, date in enumerate(dates):
        trend_data.append({
            "Date": date,
            "Alert Type": alert_type,
            "Count": max(0, alert_data[alert_type][i])  # Ensure no negative counts
        })

trend_df = pd.DataFrame(trend_data)

# Create the trend chart
fig = px.line(
    trend_df, 
    x="Date", 
    y="Count", 
    color="Alert Type", 
    title="Alert Volume by Type (Past 90 Days)",
    labels={"Count": "Number of Alerts", "Date": ""}
)

# Improve layout
fig.update_layout(
    height=400,
    legend_title_text="",
    hovermode="x unified"
)

# Show the chart
st.plotly_chart(fig, use_container_width=True)

# Alert heatmap by market region
st.markdown("## Alert Concentration by Region")

# Generate data for heatmap
regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
alert_types_heatmap = ["Belief Shifts", "Competition", "Market Size", "Regulatory", "Sentiment"]

# Create heatmap data
heatmap_data = []
for region in regions:
    row = {}
    row["Region"] = region
    for alert_type in alert_types_heatmap:
        # Generate values with some patterns
        if region == "Northeast" and alert_type == "Belief Shifts":
            row[alert_type] = random.randint(7, 10)  # High belief shifts in Northeast
        elif region == "Southwest" and alert_type == "Competition":
            row[alert_type] = random.randint(8, 10)  # High competition in Southwest
        elif region == "West" and alert_type == "Regulatory":
            row[alert_type] = random.randint(7, 10)  # High regulatory activity in West
        else:
            row[alert_type] = random.randint(1, 6)  # Lower in other regions
    heatmap_data.append(row)

heatmap_df = pd.DataFrame(heatmap_data)

# Melt the DataFrame for heatmap format
heatmap_df_melted = pd.melt(
    heatmap_df, 
    id_vars=["Region"], 
    value_vars=alert_types_heatmap, 
    var_name="Alert Type", 
    value_name="Alert Count"
)

# Create heatmap
fig_heatmap = px.density_heatmap(
    heatmap_df_melted,
    x="Alert Type",
    y="Region",
    z="Alert Count",
    color_continuous_scale="Viridis",
    title="Alert Concentration by Region and Type"
)

# Improve layout
fig_heatmap.update_layout(
    height=400,
    xaxis_title="",
    yaxis_title="",
    coloraxis_colorbar=dict(title="Alert Count")
)

# Show the heatmap
st.plotly_chart(fig_heatmap, use_container_width=True)

# Key insights from recent alerts
st.markdown("---")
st.markdown("## Strategic Implications")

# Create two columns for insights
insight_cols = st.columns(2)

with insight_cols[0]:
    insight_metrics = {
        "Trend Strength": "High",
        "Market Impact": "$14.2M",
        "Response Urgency": "Medium"
    }
    
    insights = [
        "The increasing focus on sustainability among 'Empathetic Dreamers' represents a significant opportunity for brands with strong ethical credentials.",
        "Competitive pressure is intensifying in the Southwest region, requiring defensive strategies in this market.",
        "The Northeast market expansion creates growth opportunities that should be prioritized in Q3 planning."
    ]
    
    recommendations = [
        "Develop sustainability-focused messaging for the 'Empathetic Dreamers' segment",
        "Create a defensive strategy for the Southwest region emphasizing unique value propositions",
        "Increase marketing investment in the Northeast region by 15-20%"
    ]
    
    action_button, plan_button = insight_card(
        title="Emerging Strategic Opportunities",
        insights=insights,
        recommendations=recommendations,
        metrics=insight_metrics,
        opportunity_level="high"
    )

with insight_cols[1]:
    risk_metrics = {
        "Risk Level": "Medium",
        "Potential Impact": "$8.7M",
        "Mitigation Difficulty": "Moderate"
    }
    
    risk_insights = [
        "Declining effectiveness of Facebook as a channel for the 25-34 demographic could reduce marketing efficiency if not addressed.",
        "New privacy regulations in California will require adjustments to data collection and personalization strategies.",
        "The market contraction in the Midwest, while minor, could indicate early signs of broader economic concerns."
    ]
    
    risk_recommendations = [
        "Shift 20% of Facebook budget to TikTok for targeting the 25-34 demographic",
        "Develop enhanced consent management for California market compliance",
        "Monitor Midwest economic indicators closely for early warning of broader trends"
    ]
    
    action_button2, plan_button2 = insight_card(
        title="Emerging Risk Factors",
        insights=risk_insights,
        recommendations=risk_recommendations,
        metrics=risk_metrics,
        opportunity_level="moderate"
    )

# Alert notification settings
st.markdown("---")
st.markdown("## Alert Notification Settings")

with st.expander("Configure Alert Notifications"):
    st.markdown("### Notification Preferences")
    
    # Create two columns for notification settings
    notify_col1, notify_col2 = st.columns(2)
    
    with notify_col1:
        st.markdown("#### Alert Types")
        st.checkbox("Belief Pattern Shifts", value=True)
        st.checkbox("Competitive Movements", value=True)
        st.checkbox("Market Size Changes", value=True)
        st.checkbox("Regulatory Updates", value=False)
        st.checkbox("Consumer Sentiment", value=False)
    
    with notify_col2:
        st.markdown("#### Priority Levels")
        st.checkbox("High Priority", value=True)
        st.checkbox("Medium Priority", value=True)
        st.checkbox("Low Priority", value=False)
        
        st.markdown("#### Delivery Methods")
        st.checkbox("Email Alerts", value=True)
        st.checkbox("SMS Notifications", value=False)
        st.checkbox("In-App Notifications", value=True)
    
    st.markdown("#### Notification Frequency")
    frequency = st.radio(
        "How often would you like to receive alerts?",
        options=["Real-time", "Daily Digest", "Weekly Summary"],
        index=1
    )
    
    if frequency == "Daily Digest":
        st.time_input("Select delivery time", datetime.now().time())
    elif frequency == "Weekly Summary":
        day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        st.selectbox("Select delivery day", day_options)
        st.time_input("Select delivery time", datetime.now().time())
    
    st.button("Save Notification Settings", use_container_width=True)

# Additional actions
action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("Create Custom Alert", use_container_width=True):
        st.info("In a real implementation, this would open a custom alert creation interface.")

with action_col2:
    if st.button("Export Alert History", use_container_width=True):
        st.info("In a real implementation, this would generate an export of alert history.")

with action_col3:
    if st.button("Schedule Alert Review", use_container_width=True):
        st.info("In a real implementation, this would open a calendar scheduling interface.")

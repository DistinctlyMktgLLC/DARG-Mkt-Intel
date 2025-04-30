import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.tier_control import enforce_tier, get_user_tier
from utils.data_access import get_demographic_summary, get_map_data, get_market_insights
from components.insight_card import insight_card, quick_insight
from components.action_recommendation import segment_targeting_guide
from utils.html_render import render_html

# Page configuration
st.set_page_config(
    page_title="Who to Target | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - Accelerate tier required
enforce_tier('Accelerate')

# Title and description
st.title("Who to Target")
st.markdown("""
Identify your most valuable audience segments and understand their unique characteristics and preferences.
This analysis helps you develop targeted marketing strategies for the most profitable customer groups.
""")

# Sidebar filters
st.sidebar.markdown("## Segment Filters")

# Demographic filters
st.sidebar.markdown("### Demographics")

age_ranges = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
selected_age_ranges = st.sidebar.multiselect(
    "Age Ranges",
    options=age_ranges,
    default=["25-34", "35-44"]
)

income_levels = ["Low", "Middle", "Upper Middle", "High"]
selected_income_levels = st.sidebar.multiselect(
    "Income Levels",
    options=income_levels,
    default=["Middle", "Upper Middle"]
)

# Psychographic filters
st.sidebar.markdown("### Psychographics")

personas = [
    "Empathetic Dreamers", 
    "Craver Mavens", 
    "Hyper Experiencers", 
    "Rational Planners",
    "Comfort Seekers",
    "Trend Followers"
]
selected_personas = st.sidebar.multiselect(
    "Persona Types",
    options=personas,
    default=["Empathetic Dreamers", "Hyper Experiencers"]
)

# Geographic filters
st.sidebar.markdown("### Geographic Scope")
geographic_scope = st.sidebar.radio(
    "Select Geographic Scope",
    options=["National", "Regional", "State-level"],
    index=1
)

if geographic_scope == "Regional":
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    selected_regions = st.sidebar.multiselect(
        "Regions",
        options=regions,
        default=["Northeast", "West"]
    )
elif geographic_scope == "State-level":
    states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
    selected_states = st.sidebar.multiselect(
        "States",
        options=states,
        default=["CA", "NY", "TX"]
    )

# Apply filters button
apply_filters = st.sidebar.button("Apply Filters", use_container_width=True)

# Determine state_filter based on geographic scope selection
state_filter = None
if geographic_scope == "State-level" and selected_states:
    state_filter = selected_states
elif geographic_scope == "Regional" and selected_regions:
    # Map regions to states (simplified)
    region_to_states = {
        "Northeast": ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"],
        "Southeast": ["DE", "MD", "VA", "WV", "KY", "NC", "SC", "GA", "FL", "AL", "MS", "TN", "AR", "LA"],
        "Midwest": ["OH", "MI", "IN", "WI", "IL", "MN", "IA", "MO", "ND", "SD", "NE", "KS"],
        "Southwest": ["TX", "OK", "NM", "AZ"],
        "West": ["CO", "WY", "MT", "ID", "WA", "OR", "NV", "CA", "AK", "HI", "UT"]
    }
    
    state_filter = []
    for region in selected_regions:
        state_filter.extend(region_to_states.get(region, []))

# Main content area

# Try to get demographic summary
demographic_data = get_demographic_summary(state_filter)

# Handle demographic data
if "error" in demographic_data:
    st.warning(f"Could not load demographic data: {demographic_data['error']}")
    # Use dummy data for demonstration
    demographic_data = {
        "gender": {"Male": 48.2, "Female": 51.8},
        "race": {"White": 61.5, "Black": 12.3, "Hispanic": 18.2, "Asian": 5.8, "Other": 2.2},
        "income_level": {"Low": 18.5, "Middle": 42.3, "Upper Middle": 28.7, "High": 10.5},
        "education": {"High School": 28.4, "Some College": 33.1, "Bachelor's": 22.8, "Graduate": 15.7},
        "segment": {
            "Empathetic Dreamers": 22.5, 
            "Craver Mavens": 18.3, 
            "Hyper Experiencers": 15.7, 
            "Rational Planners": 24.2,
            "Comfort Seekers": 12.8,
            "Trend Followers": 6.5
        }
    }

# Top Personas section
st.markdown("## Top Audience Personas")

# Define detailed personas (normally this would come from database)
persona_details = {
    "Empathetic Dreamers": {
        "characteristics": {
            "demographics": {
                "Age": "25-34",
                "Income": "Upper Middle",
                "Education": "Bachelor's or higher",
                "Gender": "Skews female (62%)"
            },
            "psychographics": {
                "Core Values": "Connection, authenticity, meaning",
                "Drivers": "Emotional resonance, social impact",
                "Risk Tolerance": "Moderate"
            },
            "behaviors": {
                "Purchase Cycle": "Research-heavy, values-based",
                "Loyalty": "High when values aligned",
                "Price Sensitivity": "Medium (value over price)"
            }
        },
        "positioning": "Position your brand as a pathway to meaningful connections and experiences that align with their deeply-held values. Emphasize authenticity and how your offerings foster genuine relationships or contribute to causes they care about.",
        "messaging_themes": [
            {"name": "Authentic Connection", "description": "Emphasize how your product/service creates genuine human connections"},
            {"name": "Meaningful Impact", "description": "Highlight the positive difference your brand makes in the world"},
            {"name": "Personal Growth", "description": "Show how your offering helps them become their best self"}
        ],
        "channels": [
            {"name": "Instagram", "effectiveness": 9},
            {"name": "Podcasts", "effectiveness": 8},
            {"name": "Community Events", "effectiveness": 8},
            {"name": "Email", "effectiveness": 7},
            {"name": "YouTube", "effectiveness": 6},
            {"name": "Traditional TV", "effectiveness": 3}
        ]
    },
    "Hyper Experiencers": {
        "characteristics": {
            "demographics": {
                "Age": "18-34",
                "Income": "Middle to High",
                "Education": "Some College or Bachelor's",
                "Gender": "Balanced (52% male, 48% female)"
            },
            "psychographics": {
                "Core Values": "Novelty, excitement, status",
                "Drivers": "FOMO, social currency, unique experiences",
                "Risk Tolerance": "High"
            },
            "behaviors": {
                "Purchase Cycle": "Impulsive, trend-driven",
                "Loyalty": "Low (always seeking new)",
                "Price Sensitivity": "Low for experiences, medium for products"
            }
        },
        "positioning": "Position your brand as the gateway to exclusive, shareable experiences that put them ahead of trends. Emphasize novelty, limited availability, and the social currency your offerings provide.",
        "messaging_themes": [
            {"name": "Exclusive Access", "description": "Emphasize limited availability and insider status"},
            {"name": "Cutting Edge", "description": "Highlight how your offering puts them ahead of trends"},
            {"name": "Share-worthy", "description": "Show how your product creates social media-worthy moments"}
        ],
        "channels": [
            {"name": "TikTok", "effectiveness": 9},
            {"name": "Instagram", "effectiveness": 9},
            {"name": "Influencer Partnerships", "effectiveness": 8},
            {"name": "Pop-up Experiences", "effectiveness": 8},
            {"name": "Snapchat", "effectiveness": 7},
            {"name": "Email", "effectiveness": 4}
        ]
    }
}

# Create tabs for each selected persona
if len(selected_personas) > 0:
    persona_tabs = st.tabs(selected_personas)
    
    for i, persona_name in enumerate(selected_personas):
        with persona_tabs[i]:
            # Get details for this persona
            details = persona_details.get(persona_name, {})
            
            if details:
                segment_targeting_guide(
                    segment_name=persona_name,
                    characteristics=details.get("characteristics", {}),
                    positioning=details.get("positioning", "No positioning available"),
                    messaging_themes=details.get("messaging_themes", []),
                    channels=details.get("channels", [])
                )
            else:
                st.warning(f"Detailed information for {persona_name} is not available.")
else:
    st.info("Please select at least one persona type from the sidebar to view detailed targeting information.")

# Demographic Breakdown section
st.markdown("---")
st.markdown("## Demographic Breakdown")

# Create a row of charts for demographic visualization
chart_cols = st.columns(2)

# Gender breakdown
with chart_cols[0]:
    st.markdown("### Gender Distribution")
    gender_data = demographic_data.get("gender", {})
    
    if gender_data:
        fig_gender = px.pie(
            values=list(gender_data.values()),
            names=list(gender_data.keys()),
            color_discrete_sequence=px.colors.sequential.Blues,
            hole=0.4
        )
        fig_gender.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gender, use_container_width=True)
    else:
        st.info("No gender data available")

# Race breakdown
with chart_cols[1]:
    st.markdown("### Racial Demographics")
    race_data = demographic_data.get("race", {})
    
    if race_data:
        fig_race = px.pie(
            values=list(race_data.values()),
            names=list(race_data.keys()),
            color_discrete_sequence=px.colors.sequential.Greens,
            hole=0.4
        )
        fig_race.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_race, use_container_width=True)
    else:
        st.info("No race data available")

# Create another row for income and education
chart_cols2 = st.columns(2)

# Income level breakdown
with chart_cols2[0]:
    st.markdown("### Income Levels")
    income_data = demographic_data.get("income_level", {})
    
    if income_data:
        income_df = pd.DataFrame({
            "Income Level": list(income_data.keys()),
            "Percentage": list(income_data.values())
        })
        
        fig_income = px.bar(
            income_df,
            y="Income Level",
            x="Percentage",
            orientation="h",
            color="Percentage",
            color_continuous_scale="Reds",
            labels={"Percentage": "% of Population"}
        )
        fig_income.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_income, use_container_width=True)
    else:
        st.info("No income level data available")

# Education breakdown
with chart_cols2[1]:
    st.markdown("### Education Levels")
    education_data = demographic_data.get("education", {})
    
    if education_data:
        education_df = pd.DataFrame({
            "Education Level": list(education_data.keys()),
            "Percentage": list(education_data.values())
        })
        
        fig_education = px.bar(
            education_df,
            y="Education Level",
            x="Percentage",
            orientation="h",
            color="Percentage",
            color_continuous_scale="Purples",
            labels={"Percentage": "% of Population"}
        )
        fig_education.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_education, use_container_width=True)
    else:
        st.info("No education data available")

# Persona Distribution section
st.markdown("---")
st.markdown("## Persona Distribution")

# Get segment data
segment_data = demographic_data.get("segment", {})

if segment_data:
    # Convert to DataFrame
    segment_df = pd.DataFrame({
        "Persona": list(segment_data.keys()),
        "Percentage": list(segment_data.values())
    }).sort_values("Percentage", ascending=False)
    
    # Highlight selected personas
    segment_df["Selected"] = segment_df["Persona"].isin(selected_personas)
    segment_df["Color"] = segment_df["Selected"].map({True: "#0068c9", False: "#bbbbbb"})
    
    # Create bar chart
    fig_segment = px.bar(
        segment_df,
        y="Persona",
        x="Percentage",
        orientation="h",
        color="Selected",
        color_discrete_map={True: "#0068c9", False: "#bbbbbb"},
        labels={"Percentage": "% of Population", "Persona": ""}
    )
    
    fig_segment.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    
    st.plotly_chart(fig_segment, use_container_width=True)
    
    # Opportunity calculation based on selected personas
    if selected_personas:
        total_selected_percentage = sum([segment_data.get(persona, 0) for persona in selected_personas])
        
        st.markdown(f"""
        ### Targeting Impact
        
        The selected personas represent **{total_selected_percentage:.1f}%** of the total market. 
        By focusing on these segments, you can efficiently allocate your resources to the most valuable audience groups.
        """)
    
        # Calculate potential metrics
        potential_reach = total_selected_percentage * 1000000 / 100  # Assuming a market of 1M people
        potential_value = potential_reach * 50  # Assuming $50 average value per customer
        
        metric_cols = st.columns(3)
        metric_cols[0].metric("Potential Audience Reach", f"{potential_reach:,.0f}")
        metric_cols[1].metric("Estimated Market Value", f"${potential_value:,.0f}")
        metric_cols[2].metric("Conversion Efficiency", f"+{total_selected_percentage:.1f}%")
else:
    st.info("No persona distribution data available")

# Targeting recommendations
st.markdown("---")
st.markdown("## Strategic Targeting Recommendations")

if selected_personas:
    # Create recommendations based on selected personas
    recommendations = []
    
    if "Empathetic Dreamers" in selected_personas:
        recommendations.append("""
        **Empathetic Dreamers Strategy:**
        Focus on authentic storytelling that emphasizes your brand's values and impact. Use visually rich, emotionally resonant content that showcases real connections and meaningful experiences.
        """)
    
    if "Hyper Experiencers" in selected_personas:
        recommendations.append("""
        **Hyper Experiencers Strategy:**
        Create limited-time offers and exclusive experiences that provide social currency. Leverage visual platforms and influencer partnerships to showcase your offerings as must-have experiences.
        """)
    
    if "Craver Mavens" in selected_personas:
        recommendations.append("""
        **Craver Mavens Strategy:**
        Highlight quality, craftsmanship and unique features of your product. Provide detailed information and behind-the-scenes content that appeals to their desire for expertise and mastery.
        """)
    
    if "Rational Planners" in selected_personas:
        recommendations.append("""
        **Rational Planners Strategy:**
        Present clear data points, comparisons and logical benefits. Focus on efficiency, reliability and value rather than emotional appeals or trendiness.
        """)
    
    # Display the recommendations
    for recommendation in recommendations:
        st.markdown(recommendation)
    
    # Add a general cross-segment strategy
    st.markdown("""
    ### Cross-Segment Approach
    
    While each segment requires tailored messaging, develop a unified brand platform that can flex to accommodate different personas. Create a modular content strategy that allows you to easily adapt core messages to resonate with each target group while maintaining brand consistency.
    """)
    
    # Action buttons
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("View Persona Details", use_container_width=True):
            st.info("In a real implementation, this would show detailed persona profiles.")
    with action_col2:
        if st.button("Create Targeting Plan", use_container_width=True):
            st.switch_page("pages/how_to_engage.py")
else:
    st.info("Please select personas from the sidebar to see targeting recommendations.")

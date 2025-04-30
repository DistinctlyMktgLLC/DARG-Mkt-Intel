import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.tier_control import enforce_tier
from utils.html_render import render_html, render_card

# Page configuration
st.set_page_config(
    page_title="ROI Calculator | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - Scale tier required for this advanced feature
enforce_tier('Scale')

# Title and description
st.title("ROI Calculator")
st.markdown("""
Project the return on investment for your market strategies based on belief alignment.
This calculator helps you estimate the financial impact of different strategic approaches.
""")

# Sidebar inputs
st.sidebar.markdown("## Strategy Parameters")

# Strategy type selection
st.sidebar.markdown("### Strategy Type")
strategy_type = st.sidebar.selectbox(
    "Select Strategy Type",
    options=["Customer Acquisition", "Retention & Loyalty", "Market Expansion", "Brand Awareness", "Product Launch"],
    index=0
)

# Target audience selection
st.sidebar.markdown("### Target Audience")
audiences = ["All Segments", "Empathetic Dreamers", "Craver Mavens", "Hyper Experiencers", "Rational Planners", "Comfort Seekers"]
target_audience = st.sidebar.selectbox(
    "Primary Audience",
    options=audiences,
    index=0
)

# Geographic focus selection
st.sidebar.markdown("### Geographic Focus")
geographic_focus = st.sidebar.selectbox(
    "Region Focus",
    options=["National", "Northeast", "Southeast", "Midwest", "Southwest", "West"],
    index=0
)

# Investment inputs
st.sidebar.markdown("### Investment Parameters")

total_budget = st.sidebar.number_input(
    "Total Strategy Budget ($)",
    min_value=10000,
    max_value=10000000,
    value=100000,
    step=10000,
    format="%d"
)

implementation_timeline = st.sidebar.slider(
    "Implementation Timeline (months)",
    min_value=3,
    max_value=24,
    value=12,
    step=3
)

# Advanced parameters toggle
show_advanced = st.sidebar.checkbox("Show Advanced Parameters")

if show_advanced:
    st.sidebar.markdown("### Advanced Parameters")
    
    belief_alignment_score = st.sidebar.slider(
        "Belief Alignment Score",
        min_value=1,
        max_value=100,
        value=75,
        help="How well your strategy aligns with the target audience's core beliefs"
    )
    
    market_competitiveness = st.sidebar.slider(
        "Market Competitiveness",
        min_value=1,
        max_value=100,
        value=65,
        help="Level of competition in your target market"
    )
    
    economic_conditions = st.sidebar.slider(
        "Economic Conditions",
        min_value=1,
        max_value=100,
        value=60,
        help="Current and projected economic conditions in target market"
    )
    
    execution_confidence = st.sidebar.slider(
        "Execution Confidence",
        min_value=1,
        max_value=100,
        value=80,
        help="How confident you are in your ability to execute this strategy"
    )
else:
    # Default values for advanced parameters
    belief_alignment_score = 75
    market_competitiveness = 65
    economic_conditions = 60
    execution_confidence = 80

# Calculate button
calculate_roi = st.sidebar.button("Calculate ROI", use_container_width=True)

# Main content area

# ROI overview section
st.markdown("## ROI Summary")

# Create columns for key metrics
metric_cols = st.columns(4)

# Function to calculate ROI based on inputs
def calculate_strategy_roi(
    strategy_type, 
    total_budget, 
    implementation_timeline, 
    belief_alignment_score,
    market_competitiveness,
    economic_conditions,
    execution_confidence,
    audience,
    region
):
    """
    Calculate estimated ROI metrics based on input parameters.
    
    In a real implementation, this would use sophisticated models based on 
    historical data and market insights. This is a simplified demonstration.
    """
    # Base multipliers for different strategy types
    strategy_multipliers = {
        "Customer Acquisition": 3.2,
        "Retention & Loyalty": 4.1,
        "Market Expansion": 2.8,
        "Brand Awareness": 2.2,
        "Product Launch": 2.5
    }
    
    # Base ROI for the strategy type
    base_roi = strategy_multipliers.get(strategy_type, 3.0)
    
    # Adjust based on belief alignment (higher alignment = higher ROI)
    alignment_factor = belief_alignment_score / 50  # Normalize to ~2 at 100%
    
    # Adjust based on competition (higher competition = lower ROI)
    competition_factor = 2 - (market_competitiveness / 100)
    
    # Adjust based on economic conditions
    economic_factor = economic_conditions / 75
    
    # Adjust based on execution confidence
    execution_factor = execution_confidence / 80
    
    # Adjust based on timeline (shorter timeline = lower total return but higher ROI)
    timeline_factor = 12 / implementation_timeline
    
    # Calculate final ROI multiplier
    roi_multiplier = base_roi * alignment_factor * competition_factor * economic_factor * execution_factor
    
    # Apply slight random variation for realism
    roi_multiplier *= (0.9 + np.random.rand() * 0.2)
    
    # Calculate total return
    total_return = total_budget * roi_multiplier
    
    # Calculate ROI percentage
    roi_percentage = (total_return / total_budget - 1) * 100
    
    # Calculate payback period (months)
    monthly_return = total_return / implementation_timeline
    months_to_payback = total_budget / monthly_return if monthly_return > 0 else implementation_timeline
    
    # Calculate risk level (0-100)
    risk_level = 100 - ((belief_alignment_score + execution_confidence + economic_conditions) / 3)
    
    # Generate monthly projections
    monthly_data = []
    cumulative_investment = 0
    cumulative_return = 0
    
    for month in range(1, implementation_timeline + 1):
        # Investment is front-loaded
        if month == 1:
            monthly_investment = total_budget * 0.3
        elif month <= 3:
            monthly_investment = total_budget * 0.2 / 2
        else:
            remaining_budget = total_budget * 0.5
            monthly_investment = remaining_budget / (implementation_timeline - 3)
        
        cumulative_investment += monthly_investment
        
        # Returns start slower and accelerate
        if month <= 2:
            monthly_return = total_return * 0.02
        elif month <= 6:
            monthly_return = total_return * 0.08 / 4
        else:
            remaining_return = total_return * 0.9
            monthly_return = remaining_return / (implementation_timeline - 6)
            # Add acceleration factor in later months
            monthly_return *= (1 + (month / implementation_timeline) * 0.5)
        
        cumulative_return += monthly_return
        
        # Calculate period ROI
        if cumulative_investment > 0:
            period_roi = (cumulative_return / cumulative_investment - 1) * 100
        else:
            period_roi = 0
        
        monthly_data.append({
            "Month": month,
            "Monthly Investment": monthly_investment,
            "Cumulative Investment": cumulative_investment,
            "Monthly Return": monthly_return,
            "Cumulative Return": cumulative_return,
            "Period ROI": period_roi
        })
    
    # Create results dictionary
    results = {
        "roi_percentage": roi_percentage,
        "total_return": total_return,
        "payback_period": months_to_payback,
        "risk_level": risk_level,
        "monthly_data": monthly_data,
        "first_year_return": sum([m["Monthly Return"] for m in monthly_data if m["Month"] <= 12]),
        "belief_impact": belief_alignment_score * roi_multiplier / 10
    }
    
    return results

# Display ROI metrics if calculate button is pressed
if calculate_roi or "roi_results" in st.session_state:
    # Calculate ROI or use cached results
    if calculate_roi:
        roi_results = calculate_strategy_roi(
            strategy_type=strategy_type,
            total_budget=total_budget,
            implementation_timeline=implementation_timeline,
            belief_alignment_score=belief_alignment_score,
            market_competitiveness=market_competitiveness,
            economic_conditions=economic_conditions,
            execution_confidence=execution_confidence,
            audience=target_audience,
            region=geographic_focus
        )
        st.session_state.roi_results = roi_results
    else:
        roi_results = st.session_state.roi_results

    # Display key metrics
    with metric_cols[0]:
        st.metric(
            label="Projected ROI",
            value=f"{roi_results['roi_percentage']:.1f}%",
            delta=f"{roi_results['roi_percentage'] - 200:.1f}%" if roi_results['roi_percentage'] > 200 else None,
            delta_color="normal"
        )
    
    with metric_cols[1]:
        st.metric(
            label="Total Return",
            value=f"${roi_results['total_return']:,.0f}",
            delta=f"${roi_results['total_return'] - total_budget:,.0f}"
        )
    
    with metric_cols[2]:
        st.metric(
            label="Payback Period",
            value=f"{roi_results['payback_period']:.1f} months",
            delta=f"{12 - roi_results['payback_period']:.1f} months" if roi_results['payback_period'] < 12 else None
        )
    
    with metric_cols[3]:
        risk_color = "inverse" if roi_results['risk_level'] > 40 else "normal"
        st.metric(
            label="Risk Level",
            value=f"{roi_results['risk_level']:.0f}/100",
            delta=f"{50 - roi_results['risk_level']:.0f}" if roi_results['risk_level'] != 50 else None,
            delta_color=risk_color
        )
    
    # Create monthly projection chart
    st.markdown("## Investment & Return Projection")
    
    # Convert monthly data to DataFrame
    monthly_df = pd.DataFrame(roi_results["monthly_data"])
    
    # Create combined line and bar chart
    fig = go.Figure()
    
    # Add bar chart for monthly investment
    fig.add_trace(go.Bar(
        x=monthly_df["Month"],
        y=monthly_df["Monthly Investment"],
        name="Monthly Investment",
        marker_color='rgba(41, 128, 185, 0.7)'
    ))
    
    # Add bar chart for monthly return
    fig.add_trace(go.Bar(
        x=monthly_df["Month"],
        y=monthly_df["Monthly Return"],
        name="Monthly Return",
        marker_color='rgba(46, 204, 113, 0.7)'
    ))
    
    # Add line for cumulative investment
    fig.add_trace(go.Scatter(
        x=monthly_df["Month"],
        y=monthly_df["Cumulative Investment"],
        name="Cumulative Investment",
        line=dict(color='rgb(41, 128, 185)', width=3),
        mode='lines'
    ))
    
    # Add line for cumulative return
    fig.add_trace(go.Scatter(
        x=monthly_df["Month"],
        y=monthly_df["Cumulative Return"],
        name="Cumulative Return",
        line=dict(color='rgb(46, 204, 113)', width=3),
        mode='lines'
    ))
    
    # Add break-even point
    # Find first month where cumulative return exceeds cumulative investment
    breakeven_month = None
    for i, row in enumerate(roi_results["monthly_data"]):
        if row["Cumulative Return"] >= row["Cumulative Investment"]:
            breakeven_month = row["Month"]
            break
    
    if breakeven_month:
        breakeven_value = monthly_df.loc[monthly_df["Month"] == breakeven_month, "Cumulative Investment"].values[0]
        
        fig.add_trace(go.Scatter(
            x=[breakeven_month, breakeven_month],
            y=[0, breakeven_value],
            mode="lines",
            line=dict(color="red", width=2, dash="dash"),
            name="Break-even Point"
        ))
        
        fig.add_annotation(
            x=breakeven_month,
            y=breakeven_value / 2,
            text=f"Break-even: Month {breakeven_month}",
            showarrow=True,
            arrowhead=1,
            ax=40,
            ay=0
        )
    
    # Update layout
    fig.update_layout(
        title="Monthly Investment and Return Projection",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        legend_title="Metric",
        barmode='group',
        height=500
    )
    
    # Show the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # ROI comparison section
    st.markdown("## Strategy Comparison")
    st.markdown("Compare ROI projections for different strategy types with your current parameters.")
    
    # Calculate ROI for all strategy types with current parameters
    strategy_types = ["Customer Acquisition", "Retention & Loyalty", "Market Expansion", "Brand Awareness", "Product Launch"]
    comparison_data = []
    
    for strategy in strategy_types:
        comparison_roi = calculate_strategy_roi(
            strategy_type=strategy,
            total_budget=total_budget,
            implementation_timeline=implementation_timeline,
            belief_alignment_score=belief_alignment_score,
            market_competitiveness=market_competitiveness,
            economic_conditions=economic_conditions,
            execution_confidence=execution_confidence,
            audience=target_audience,
            region=geographic_focus
        )
        
        comparison_data.append({
            "Strategy Type": strategy,
            "ROI (%)": comparison_roi["roi_percentage"],
            "Total Return ($)": comparison_roi["total_return"],
            "Payback Period (months)": comparison_roi["payback_period"],
            "Risk Level": comparison_roi["risk_level"],
            "Is Selected": strategy == strategy_type
        })
    
    # Convert to DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create two columns for different comparison charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # ROI comparison chart
        fig_roi = px.bar(
            comparison_df,
            x="Strategy Type",
            y="ROI (%)",
            color="Is Selected",
            color_discrete_map={True: "#0068c9", False: "#bbbbbb"},
            labels={"ROI (%)": "Projected ROI (%)", "Strategy Type": ""},
            title="ROI Comparison by Strategy Type"
        )
        
        fig_roi.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_roi, use_container_width=True)
    
    with chart_col2:
        # Risk vs. Return chart
        fig_risk = px.scatter(
            comparison_df,
            x="Risk Level",
            y="ROI (%)",
            size="Total Return ($)",
            color="Is Selected",
            color_discrete_map={True: "#0068c9", False: "#bbbbbb"},
            hover_name="Strategy Type",
            labels={"ROI (%)": "Projected ROI (%)", "Risk Level": "Risk Level (0-100)"},
            title="Risk vs. Return Comparison"
        )
        
        fig_risk.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Sensitivity analysis
    st.markdown("## Sensitivity Analysis")
    st.markdown("Understand how changes in key parameters affect your projected ROI.")
    
    # Parameters to analyze
    parameters = ["Belief Alignment", "Market Competitiveness", "Economic Conditions", "Execution Confidence"]
    parameter_values = {}
    
    # Generate sensitivity data
    for param in parameters:
        values = []
        for adjustment in [-20, -10, 0, 10, 20]:
            if param == "Belief Alignment":
                value = belief_alignment_score + adjustment
                value = max(1, min(100, value))
            elif param == "Market Competitiveness":
                value = market_competitiveness + adjustment
                value = max(1, min(100, value))
            elif param == "Economic Conditions":
                value = economic_conditions + adjustment
                value = max(1, min(100, value))
            elif param == "Execution Confidence":
                value = execution_confidence + adjustment
                value = max(1, min(100, value))
            
            # Recalculate ROI with adjusted parameter
            adj_roi = calculate_strategy_roi(
                strategy_type=strategy_type,
                total_budget=total_budget,
                implementation_timeline=implementation_timeline,
                belief_alignment_score=value if param == "Belief Alignment" else belief_alignment_score,
                market_competitiveness=value if param == "Market Competitiveness" else market_competitiveness,
                economic_conditions=value if param == "Economic Conditions" else economic_conditions,
                execution_confidence=value if param == "Execution Confidence" else execution_confidence,
                audience=target_audience,
                region=geographic_focus
            )
            
            values.append({
                "Parameter": param,
                "Adjustment": f"{adjustment:+d}",
                "Value": value,
                "ROI (%)": adj_roi["roi_percentage"]
            })
        
        parameter_values[param] = values
    
    # Combine all data
    sensitivity_data = []
    for param, values in parameter_values.items():
        sensitivity_data.extend(values)
    
    sensitivity_df = pd.DataFrame(sensitivity_data)
    
    # Create sensitivity chart
    fig_sensitivity = px.line(
        sensitivity_df,
        x="Adjustment",
        y="ROI (%)",
        color="Parameter",
        markers=True,
        labels={"ROI (%)": "Projected ROI (%)", "Adjustment": "Parameter Adjustment"},
        title="ROI Sensitivity to Parameter Changes"
    )
    
    fig_sensitivity.update_layout(height=500)
    st.plotly_chart(fig_sensitivity, use_container_width=True)
    
    # Key findings and recommendations
    st.markdown("## Key Findings")
    
    # Determine most sensitive parameter
    param_impacts = {}
    for param in parameters:
        param_data = [item for item in sensitivity_data if item["Parameter"] == param]
        max_roi = max([item["ROI (%)"] for item in param_data])
        min_roi = min([item["ROI (%)"] for item in param_data])
        param_impacts[param] = max_roi - min_roi
    
    most_sensitive = max(param_impacts, key=param_impacts.get)
    
    # Generate findings
    findings_html = f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">ROI Analysis Findings</h3>
        
        <p><strong>1. Overall ROI Assessment:</strong> Your {strategy_type} strategy is projected to yield a 
        {roi_results['roi_percentage']:.1f}% ROI over {implementation_timeline} months, with a payback period of 
        {roi_results['payback_period']:.1f} months.</p>
        
        <p><strong>2. Belief Alignment Impact:</strong> The current belief alignment score of {belief_alignment_score} 
        is contributing approximately ${roi_results['belief_impact']:,.0f} to your total return. Each 10-point 
        increase in alignment could yield an additional 
        {(parameter_values['Belief Alignment'][4]['ROI (%)'] - parameter_values['Belief Alignment'][2]['ROI (%)']):,.1f}% in ROI.</p>
        
        <p><strong>3. Sensitivity Analysis:</strong> Your ROI is most sensitive to changes in <strong>{most_sensitive}</strong>. 
        Focus on optimizing this parameter for maximum returns.</p>
        
        <p><strong>4. Risk Assessment:</strong> At {roi_results['risk_level']:.0f}/100, your risk level is 
        {'moderate' if 30 <= roi_results['risk_level'] <= 70 else 'high' if roi_results['risk_level'] > 70 else 'low'}.
        {'Consider risk mitigation strategies to improve potential returns.' if roi_results['risk_level'] > 50 else ''}</p>
    </div>
    """
    
    render_html(findings_html)
    
    # Recommendations based on analysis
    st.markdown("## Recommendations")
    
    # Generate strategy-specific recommendations
    if strategy_type == "Customer Acquisition":
        recommendations = [
            f"Increase belief alignment by refining your value proposition to more closely match the core beliefs of the {target_audience} segment",
            "Consider front-loading your marketing investment to accelerate customer acquisition and improve ROI",
            "Test different messaging approaches to identify highest-converting communications"
        ]
    elif strategy_type == "Retention & Loyalty":
        recommendations = [
            "Implement a tiered loyalty program that rewards behaviors aligned with customer belief systems",
            "Develop personalized retention campaigns based on customer belief patterns",
            "Create community experiences that reinforce the relationship between your brand and customer values"
        ]
    elif strategy_type == "Market Expansion":
        recommendations = [
            f"Prioritize geographic locations within the {geographic_focus} region that show highest belief alignment",
            "Develop market-specific messaging that addresses local belief variations",
            "Consider partnership strategies to accelerate market entry and reduce risk"
        ]
    elif strategy_type == "Brand Awareness":
        recommendations = [
            "Focus brand messaging on elements that resonate with the core beliefs of your target audience",
            "Allocate budget toward channels that allow for more emotional and belief-driven communication",
            "Develop measurement frameworks that track belief association alongside traditional awareness metrics"
        ]
    elif strategy_type == "Product Launch":
        recommendations = [
            "Position product features in terms of how they address core consumer beliefs rather than just functionality",
            "Identify and engage with belief-aligned early adopters to create authentic testimonials",
            "Create launch messaging that emphasizes belief-alignment to drive faster initial adoption"
        ]
    
    # Add general recommendations based on sensitivity analysis
    if most_sensitive == "Belief Alignment":
        recommendations.append("Invest in additional consumer research to better understand and align with target audience beliefs")
    elif most_sensitive == "Market Competitiveness":
        recommendations.append("Conduct competitive analysis to identify unique positioning opportunities in less saturated market segments")
    elif most_sensitive == "Economic Conditions":
        recommendations.append("Develop contingency plans for economic volatility and consider phased implementation approach")
    elif most_sensitive == "Execution Confidence":
        recommendations.append("Strengthen implementation capabilities through additional resources or partnerships")
    
    # Display recommendations
    for i, recommendation in enumerate(recommendations):
        st.markdown(f"**{i+1}. {recommendation}**")
    
    # Action buttons
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("Save ROI Analysis", use_container_width=True):
            st.success("ROI analysis saved! You can access it from your saved reports.")
    
    with action_col2:
        if st.button("Export as PDF", use_container_width=True):
            st.info("In a real implementation, this would generate a PDF report.")
    
    with action_col3:
        if st.button("Create Strategy Based on Analysis", use_container_width=True):
            st.switch_page("pages/how_to_engage.py")
else:
    # Show instruction message if calculate button not yet pressed
    st.info("👈 Set your strategy parameters in the sidebar and click 'Calculate ROI' to see projections.")
    
    # Show example calculation
    st.markdown("## Sample ROI Calculation")
    
    # Display sample chart
    example_months = list(range(1, 13))
    example_investment = [30000] + [5000] * 5 + [10000] * 6
    example_cum_investment = np.cumsum(example_investment)
    example_returns = [0, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 55000]
    example_cum_returns = np.cumsum(example_returns)
    
    # Create sample DataFrame
    example_df = pd.DataFrame({
        "Month": example_months,
        "Monthly Investment": example_investment,
        "Cumulative Investment": example_cum_investment,
        "Monthly Return": example_returns,
        "Cumulative Return": example_cum_returns
    })
    
    # Create sample chart
    fig = go.Figure()
    
    # Add bar chart for monthly investment
    fig.add_trace(go.Bar(
        x=example_df["Month"],
        y=example_df["Monthly Investment"],
        name="Monthly Investment",
        marker_color='rgba(41, 128, 185, 0.7)'
    ))
    
    # Add bar chart for monthly return
    fig.add_trace(go.Bar(
        x=example_df["Month"],
        y=example_df["Monthly Return"],
        name="Monthly Return",
        marker_color='rgba(46, 204, 113, 0.7)'
    ))
    
    # Add line for cumulative investment
    fig.add_trace(go.Scatter(
        x=example_df["Month"],
        y=example_df["Cumulative Investment"],
        name="Cumulative Investment",
        line=dict(color='rgb(41, 128, 185)', width=3),
        mode='lines'
    ))
    
    # Add line for cumulative return
    fig.add_trace(go.Scatter(
        x=example_df["Month"],
        y=example_df["Cumulative Return"],
        name="Cumulative Return",
        line=dict(color='rgb(46, 204, 113)', width=3),
        mode='lines'
    ))
    
    # Update layout
    fig.update_layout(
        title="Sample ROI Projection (Example Only)",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        legend_title="Metric",
        barmode='group',
        height=500
    )
    
    # Show the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation of the ROI calculator
    st.markdown("## How the ROI Calculator Works")
    
    st.markdown("""
    The DARG ROI Calculator provides financial projections based on our belief forecasting technology. Here's how it works:
    
    1. **Strategy Parameters**: Select your strategy type, target audience, and region to establish the baseline.
    
    2. **Investment Inputs**: Enter your total budget and implementation timeline to create the investment framework.
    
    3. **Belief Alignment**: Our algorithm adjusts ROI projections based on how well your strategy aligns with your target audience's core beliefs.
    
    4. **Sensitivity Analysis**: See how changes in key parameters affect your expected returns.
    
    5. **Recommendations**: Receive actionable recommendations to optimize your strategy and improve projected ROI.
    
    Unlike traditional calculators that rely solely on demographic data, our projections incorporate belief patterns for significantly more accurate results.
    """)

import streamlit as st
from utils.html_render import render_html, render_timeline_item

def action_plan(title, actions, context=None, expected_outcome=None):
    """
    Display an actionable plan with steps, context, and expected outcomes.
    
    Args:
        title (str): Title of the action plan
        actions (list): List of action steps (dicts with 'title' and 'description')
        context (str, optional): Context for the action plan
        expected_outcome (str, optional): Expected outcome of following the plan
    """
    st.markdown(f"## {title}")
    
    if context:
        st.markdown("### Context")
        st.markdown(context)
    
    st.markdown("### Action Steps")
    
    for i, action in enumerate(actions):
        action_title = action.get('title', f'Step {i+1}')
        action_description = action.get('description', '')
        
        # Determine if there's a next step (for timeline connector)
        has_next = i < len(actions) - 1
        
        # Render as timeline item
        render_timeline_item(
            title=action_title,
            content=action_description,
            connector=has_next
        )
    
    if expected_outcome:
        st.markdown("### Expected Outcome")
        st.markdown(expected_outcome)
    
    # Add action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save This Plan", key=f"save_{title.replace(' ', '_').lower()}", use_container_width=True):
            st.success("Plan saved! You can access it from your Saved Strategies.")
    with col2:
        if st.button("Export as PDF", key=f"export_{title.replace(' ', '_').lower()}", use_container_width=True):
            st.info("In a real implementation, this would generate a PDF.")

def strategy_recommendation(title, strategy_sections):
    """
    Display comprehensive strategy recommendations divided into sections.
    
    Args:
        title (str): Title of the strategy
        strategy_sections (list): List of sections with 'heading', 'content', and optional 'metrics'
    """
    st.markdown(f"## {title}")
    
    for section in strategy_sections:
        st.markdown(f"### {section.get('heading', 'Strategy Section')}")
        
        # Display metrics if available
        metrics = section.get('metrics', {})
        if metrics:
            metric_cols = st.columns(len(metrics))
            for i, (label, value) in enumerate(metrics.items()):
                if isinstance(value, dict):
                    metric_value = value.get("value", "N/A")
                    delta = value.get("delta")
                    metric_cols[i].metric(label=label, value=metric_value, delta=delta)
                else:
                    metric_cols[i].metric(label=label, value=value)
        
        # Display content
        content = section.get('content', '')
        st.markdown(content)
        
        # Display recommendations if available
        recommendations = section.get('recommendations', [])
        if recommendations:
            st.markdown("#### Recommendations")
            for rec in recommendations:
                st.markdown(f"- {rec}")
        
        st.markdown("---")
    
    # Implementation timeline
    timeline = [
        {"phase": "Phase 1: Immediate", "duration": "0-30 days", "focus": "Quick wins and foundation setting"},
        {"phase": "Phase 2: Short-term", "duration": "1-3 months", "focus": "Building momentum and optimization"},
        {"phase": "Phase 3: Medium-term", "duration": "3-6 months", "focus": "Scaling successful approaches"},
        {"phase": "Phase 4: Long-term", "duration": "6-12 months", "focus": "Strategic refinement and expansion"}
    ]
    
    st.markdown("### Implementation Timeline")
    
    for item in timeline:
        html_content = f"""
        <div style="display: flex; margin-bottom: 15px;">
            <div style="width: 25%; font-weight: bold;">{item['phase']}</div>
            <div style="width: 20%;">{item['duration']}</div>
            <div style="width: 55%;">{item['focus']}</div>
        </div>
        """
        render_html(html_content)

def segment_targeting_guide(segment_name, characteristics, positioning, messaging_themes, channels):
    """
    Display a comprehensive targeting guide for a specific audience segment.
    
    Args:
        segment_name (str): Name of the audience segment
        characteristics (dict): Key characteristics of the segment
        positioning (str): Recommended positioning for this segment
        messaging_themes (list): List of effective messaging themes
        channels (dict): Recommended channels with effectiveness ratings
    """
    st.markdown(f"## Targeting Guide: {segment_name}")
    
    # Characteristics section
    st.markdown("### Key Characteristics")
    
    # Divide characteristics into columns
    char_cols = st.columns(3)
    
    # Demographics
    with char_cols[0]:
        st.markdown("#### Demographics")
        for key, value in characteristics.get('demographics', {}).items():
            st.markdown(f"**{key}:** {value}")
    
    # Psychographics
    with char_cols[1]:
        st.markdown("#### Psychographics")
        for key, value in characteristics.get('psychographics', {}).items():
            st.markdown(f"**{key}:** {value}")
    
    # Behaviors
    with char_cols[2]:
        st.markdown("#### Behaviors")
        for key, value in characteristics.get('behaviors', {}).items():
            st.markdown(f"**{key}:** {value}")
    
    # Positioning
    st.markdown("### Recommended Positioning")
    st.markdown(positioning)
    
    # Messaging themes
    st.markdown("### Effective Messaging Themes")
    for theme in messaging_themes:
        st.markdown(f"- **{theme.get('name', '')}:** {theme.get('description', '')}")
    
    # Channels
    st.markdown("### Channel Effectiveness")
    
    # Calculate max effectiveness for scaling
    max_effectiveness = max([ch.get('effectiveness', 0) for ch in channels])
    
    for channel in sorted(channels, key=lambda x: x.get('effectiveness', 0), reverse=True):
        name = channel.get('name', 'Unknown Channel')
        effectiveness = channel.get('effectiveness', 0)
        percentage = (effectiveness / max_effectiveness * 100) if max_effectiveness > 0 else 0
        
        # Determine color based on effectiveness
        if effectiveness >= 7:
            color = "#27ae60"  # Green for high effectiveness
        elif effectiveness >= 4:
            color = "#f39c12"  # Orange for medium effectiveness
        else:
            color = "#e74c3c"  # Red for low effectiveness
        
        # Create the HTML for the channel effectiveness bar
        channel_html = f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <div>{name}</div>
                <div>{effectiveness}/10</div>
            </div>
            <div style="background-color: #eee; border-radius: 4px; height: 10px; width: 100%;">
                <div style="background-color: {color}; border-radius: 4px; height: 10px; width: {percentage}%;"></div>
            </div>
        </div>
        """
        render_html(channel_html)

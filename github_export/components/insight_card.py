import streamlit as st
from utils.html_render import render_html

def insight_card(title, insights, recommendations, metrics=None, opportunity_level="moderate"):
    """
    Render an insight card with enhanced interactive features and visual elements.
    
    Args:
        title (str): Card title
        insights (list): List of insight strings
        recommendations (list): List of recommendation strings
        metrics (dict, optional): Dictionary of metrics to display
        opportunity_level (str, optional): Level of opportunity (high, moderate, low)
    """
    # Set color and icon based on opportunity level
    color_map = {
        "high": "#27ae60",      # Green
        "moderate": "#f39c12",  # Orange
        "low": "#7f8c8d"        # Gray
    }
    
    icon_map = {
        "high": "🚀",
        "moderate": "📈",
        "low": "ℹ️"
    }
    
    color = color_map.get(opportunity_level.lower(), color_map["moderate"])
    icon = icon_map.get(opportunity_level.lower(), "📊")
    
    # Initialize session state for interactivity
    card_id = f"card_{title.replace(' ', ' _').lower()}"
    if card_id not in st.session_state:
        st.session_state[card_id] = {
            "expanded": False,
            "insight_index": -1
        }
    
    # Create enhanced card container with shadow and rounded corners
    st.markdown(f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 0;
                margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                transition: box-shadow 0.3s ease;">
    </div>
    """, unsafe_allow_html=True)
    
    card = st.container()
    
    with card:
        # Enhanced header with icon and animated opportunity level indicator
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            header_html = f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="background-color: {color}; width: 32px; height: 32px; border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; 
                            margin-right: 12px; font-size: 18px; color: white;">
                    {icon}
                </div>
                <h3 style="margin: 0; color: #2c3e50;">{title}</h3>
            </div>
            """
            render_html(header_html)
            
        with header_col2:
            opportunity_html = f"""
            <div style="text-align: right;">
                <div style="display: inline-block; background-color: {color}; color: white; 
                           padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {opportunity_level.upper()} PRIORITY
                </div>
            </div>
            """
            render_html(opportunity_html)
        
        # Enhanced metrics section with visual indicators
        if metrics:
            metric_container = st.container()
            with metric_container:
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 10px; margin: 10px 0;">
                </div>
                """, unsafe_allow_html=True)
                
                metric_cols = st.columns(len(metrics))
                for i, (label, value) in enumerate(metrics.items()):
                    with metric_cols[i]:
                        if isinstance(value, dict):
                            metric_value = value.get("value", "N/A")
                            delta = value.get("delta")
                            
                            # Enhanced metric with better formatting
                            st.metric(
                                label=label,
                                value=metric_value,
                                delta=delta,
                                delta_color="normal"
                            )
                            
                            # Add a visual progress bar if the value appears to be numeric
                            try:
                                # Extract numeric value for visualization
                                numeric_str = ''.join(c for c in str(metric_value) if c.isdigit() or c == '.')
                                if numeric_str:
                                    numeric_value = float(numeric_str)
                                    # Calculate a reasonable percentage (capped at 100%)
                                    percentage = min(100, numeric_value if numeric_value < 100 else numeric_value/100)
                                    
                                    progress_html = f"""
                                    <div style="height: 4px; background-color: #e0e0e0; border-radius: 2px; margin-top: 5px;">
                                        <div style="width: {percentage}%; height: 100%; background-color: {color}; border-radius: 2px;"></div>
                                    </div>
                                    <div style="font-size: 10px; color: #7f8c8d; text-align: right; margin-top: 2px;">
                                        {percentage:.0f}% of target
                                    </div>
                                    """
                                    render_html(progress_html)
                            except:
                                pass
                        else:
                            st.metric(label=label, value=value)
        
        # Enhanced insights section with interactive elements
        st.markdown(f"""
        <div style="margin-top: 20px; border-left: 3px solid {color}; padding-left: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">Key Insights</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Create interactive insights
        for i, insight in enumerate(insights):
            is_highlighted = st.session_state[card_id]["insight_index"] == i
            bg_color = f"rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.2)) for j in (0, 2, 4))}, 0.3)" if is_highlighted else "transparent"
            
            insight_html = f"""
            <div style="padding: 8px; border-radius: 6px; margin-bottom: 8px; 
                      background-color: {bg_color}; cursor: pointer;
                      transition: all 0.2s ease;"
                 onmouseover="this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.2)) for j in (0, 2, 4))}, 0.15)';"
                 onmouseout="this.style.backgroundColor='{bg_color}';"
                 onclick="this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.2)) for j in (0, 2, 4))}, 0.3)';
                          parent.postMessage({{insight_index: {i}, card_id: '{card_id}'}}, '*');">
                <div style="display: flex; align-items: start;">
                    <div style="color: {color}; margin-right: 10px; font-size: 18px;">•</div>
                    <div style="flex: 1;">{insight}</div>
                    <div style="color: #7f8c8d; font-size: 16px; margin-left: 5px;">👆</div>
                </div>
            </div>
            """
            render_html(insight_html)
            
            # If this insight is highlighted, show details
            if is_highlighted:
                with st.expander("More Details", expanded=True):
                    st.markdown(f"""
                    This insight is based on analysis of market data trends and competitive intelligence.
                    Click on recommendations below to see suggested actions based on this insight.
                    """)
        
        # Enhanced recommendations section with visual indicators
        st.markdown(f"""
        <div style="margin-top: 20px; border-left: 3px solid {color}; padding-left: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">Recommended Actions</h4>
        </div>
        """, unsafe_allow_html=True)
        
        for i, recommendation in enumerate(recommendations):
            # Create an interactive recommendation card with hover effects
            rec_html = f"""
            <div style="display: flex; padding: 10px; border-radius: 6px; margin-bottom: 10px;
                       background-color: rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.9)) for j in (0, 2, 4))}, 0.05);
                       transition: all 0.2s ease; cursor: pointer;"
                 onmouseover="this.style.transform='translateX(5px)'; 
                            this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.9)) for j in (0, 2, 4))}, 0.1)';"
                 onmouseout="this.style.transform='translateX(0)';
                           this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.9)) for j in (0, 2, 4))}, 0.05)';">
                <div style="background-color: {color}; color: white; width: 24px; height: 24px;
                           border-radius: 50%; display: flex; align-items: center; justify-content: center;
                           margin-right: 10px; font-weight: bold;">{i+1}</div>
                <div style="flex: 1;">{recommendation}</div>
            </div>
            """
            render_html(rec_html)
        
        # Enhanced action buttons with better styling and functionality
        st.markdown("""<div style="margin-top: 20px;"></div>""", unsafe_allow_html=True)
        action_col1, action_col2, expand_col = st.columns([5, 5, 2])
        
        with action_col1:
            action_button = st.button(
                f"{icon} View Detailed Analysis", 
                key=f"view_{title.replace(' ', '_').lower()}", 
                use_container_width=True,
                type="primary"
            )
            
        with action_col2:
            plan_button = st.button(
                "📋 Create Action Plan", 
                key=f"plan_{title.replace(' ', '_').lower()}", 
                use_container_width=True
            )
            
        with expand_col:
            expand_icon = "🔽" if not st.session_state[card_id]["expanded"] else "🔼"
            if st.button(
                expand_icon,
                key=f"expand_{title.replace(' ', '_').lower()}"
            ):
                st.session_state[card_id]["expanded"] = not st.session_state[card_id]["expanded"]
                st.rerun()  # Updated from deprecated st.experimental_rerun()
        
        # Show extended content if expanded
        if st.session_state[card_id]["expanded"]:
            with st.expander("Additional Analysis", expanded=True):
                st.markdown(f"""
                #### Impact Assessment
                
                This opportunity has been evaluated based on:
                - Market growth trajectory
                - Alignment with current business capabilities
                - Competitive landscape
                - Estimated resource requirements
                
                **Overall assessment:** {opportunity_level.title()} priority for immediate action.
                """)
                
                # Add a visual progress tracker
                steps = ["Research", "Planning", "Implementation", "Evaluation"]
                current_step = 1  # For demonstration purposes
                
                st.markdown("#### Implementation Progress")
                
                progress_html = f"""
                <div style="display: flex; margin: 20px 0;">
                """
                
                for i, step in enumerate(steps):
                    step_color = color if i < current_step else "#e0e0e0"
                    step_text_color = "#ffffff" if i < current_step else "#7f8c8d"
                    progress_html += f"""
                    <div style="flex: 1; text-align: center;">
                        <div style="background-color: {step_color}; color: {step_text_color}; padding: 8px 0;
                                  border-radius: {20 if i == 0 else 0}px 0 0 {20 if i == 0 else 0}px;">
                            {step}
                        </div>
                    </div>
                    """
                    
                    # Add connector if not the last step
                    if i < len(steps) - 1:
                        connector_color = color if i < current_step - 1 else "#e0e0e0"
                        progress_html += f"""
                        <div style="width: 20px; margin-top: 8px;">
                            <div style="height: 2px; background-color: {connector_color};"></div>
                        </div>
                        """
                        
                progress_html += """
                </div>
                """
                render_html(progress_html)
    
    # Return a reference to the buttons for handling interactions
    return action_button, plan_button

def quick_insight(title, content, icon="ℹ️", color="#3498db"):
    """
    Render a small, focused insight with icon and interactive elements.
    
    Args:
        title (str): Insight title
        content (str): Insight content text
        icon (str, optional): Emoji icon
        color (str, optional): Accent color
    """
    # Create a unique ID for this insight
    insight_id = f"quick_{title.replace(' ', '_').lower()}"
    
    # Initialize session state for interactivity
    if insight_id not in st.session_state:
        st.session_state[insight_id] = {
            "expanded": False,
            "reactions": {"👍": 0, "👎": 0, "🤔": 0}
        }
    
    # Create a more engaging card with hover effects and subtle animations
    html_content = f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; 
                margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                transition: transform 0.3s ease, box-shadow 0.3s ease;"
         onmouseover="this.style.transform='translateY(-3px)'; 
                     this.style.boxShadow='0 8px 15px rgba(0,0,0,0.1)';"
         onmouseout="this.style.transform='translateY(0)'; 
                    this.style.boxShadow='0 2px 5px rgba(0,0,0,0.05)';">
        <div style="background-color: {color}; padding: 12px 15px; display: flex; align-items: center;">
            <div style="background-color: rgba(255,255,255,0.2); width: 32px; height: 32px; 
                       border-radius: 50%; display: flex; align-items: center; 
                       justify-content: center; margin-right: 12px; font-size: 18px; color: white;">
                {icon}
            </div>
            <div style="color: white; font-weight: 600; font-size: 16px;">{title}</div>
        </div>
        <div style="padding: 15px; background-color: white;">
            <p style="margin: 0; color: #333; line-height: 1.5;">{content}</p>
        </div>
    </div>
    """
    render_html(html_content)
    
    # Add interactive elements in columns
    button_cols = st.columns([5, 1, 1, 1])
    
    # Action button in first column
    with button_cols[0]:
        more_button = st.button(
            "View Details", 
            key=f"more_{insight_id}",
            use_container_width=True
        )
    
    # Reaction buttons in remaining columns
    for i, emoji in enumerate(["👍", "👎", "🤔"]):
        with button_cols[i+1]:
            count = st.session_state[insight_id]["reactions"][emoji]
            if st.button(
                f"{emoji} {count if count > 0 else ''}", 
                key=f"{emoji}_{insight_id}"
            ):
                st.session_state[insight_id]["reactions"][emoji] += 1
                st.rerun()  # Updated from deprecated st.experimental_rerun()
    
    # Show expanded content if "View Details" is clicked
    if more_button:
        st.session_state[insight_id]["expanded"] = True
    
    if st.session_state[insight_id]["expanded"]:
        with st.expander("Additional Context", expanded=True):
            st.markdown(f"""
            ### {title} - Detailed Analysis
            
            {content}
            
            #### Source Information
            This insight was derived from:
            - Analysis of market trend data
            - Consumer preference surveys
            - Industry benchmarking studies
            
            #### Suggested Applications
            Consider applying this insight to:
            - Marketing strategy development
            - Product positioning refinement
            - Customer experience enhancements
            """)
            
            # Add follow-up options
            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("Generate Report", key=f"report_{insight_id}", use_container_width=True):
                    st.info("Generating comprehensive report... (This would connect to reporting functionality)")
            with action_cols[1]:
                if st.button("Close Details", key=f"close_{insight_id}", use_container_width=True):
                    st.session_state[insight_id]["expanded"] = False
                    st.rerun()  # Updated from deprecated st.experimental_rerun()
                    
    return more_button

def comparison_insight(title, items, direction="higher_better"):
    """
    Render an enhanced comparison insight showing multiple items with visual indicators.
    
    Args:
        title (str): Comparison title
        items (list): List of dicts with 'name' and 'value' keys
        direction (str): 'higher_better' or 'lower_better' to determine colors
    """
    if not items:
        st.warning(f"No data available for {title}")
        return
    
    # Create a unique ID for this comparison
    comparison_id = f"compare_{title.replace(' ', '_').lower()}"
    
    # Initialize session state for interactivity
    if comparison_id not in st.session_state:
        st.session_state[comparison_id] = {
            "sort_order": "default",
            "show_details": False,
            "highlighted_item": None
        }
    
    # Header with sort options
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h4 style="margin: 0; color: #2c3e50;">{title}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Add sort options
    sort_col1, sort_col2, sort_col3 = st.columns([1, 1, 2])
    with sort_col1:
        if st.button("Highest First", key=f"highest_{comparison_id}", use_container_width=True):
            st.session_state[comparison_id]["sort_order"] = "highest"
            st.rerun()  # Updated from deprecated st.experimental_rerun()
            
    with sort_col2:
        if st.button("Lowest First", key=f"lowest_{comparison_id}", use_container_width=True):
            st.session_state[comparison_id]["sort_order"] = "lowest"
            st.rerun()  # Updated from deprecated st.experimental_rerun()
    
    # Sort the items based on selected order
    sort_order = st.session_state[comparison_id]["sort_order"]
    if sort_order == "highest":
        sorted_items = sorted(items, key=lambda x: float(x.get('value', 0)), reverse=True)
    elif sort_order == "lowest":
        sorted_items = sorted(items, key=lambda x: float(x.get('value', 0)), reverse=False)
    else:
        # Default sort (higher or lower better)
        sorted_items = sorted(items, key=lambda x: float(x.get('value', 0)), reverse=(direction == 'higher_better'))
    
    # Generate a bar for each item
    max_value = max([float(item.get('value', 0)) for item in items])
    
    # Create an enhanced container for the comparison
    st.markdown(f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-top: 10px;">
    </div>
    """, unsafe_allow_html=True)
    
    # Add interactive elements
    for i, item in enumerate(sorted_items):
        name = item.get('name', 'Unknown')
        value = float(item.get('value', 0))
        percentage = (value / max_value * 100) if max_value > 0 else 0
        
        # Determine color based on direction and position
        position = "top" if i == 0 else "bottom" if i == len(sorted_items) - 1 else "middle"
        
        if position == "top":
            color = "#27ae60" if direction == "higher_better" else "#e74c3c"  # Green or Red
            indicator = "⭐" if direction == "higher_better" else "⚠️"
            tooltip = "Top performer" if direction == "higher_better" else "Needs attention"
        elif position == "bottom":
            color = "#e74c3c" if direction == "higher_better" else "#27ae60"  # Red or Green
            indicator = "⚠️" if direction == "higher_better" else "⭐"
            tooltip = "Needs improvement" if direction == "higher_better" else "Best performer"
        else:
            color = "#f39c12"  # Orange for middle items
            indicator = "▪️"
            tooltip = "Average performance"
        
        # Check if this item is highlighted
        is_highlighted = st.session_state[comparison_id]["highlighted_item"] == name
        bg_color = f"rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.1)) for j in (0, 2, 4))}, 0.3)" if is_highlighted else "transparent"
        
        # Create interactive bar component with hover and click effects
        bar_html = f"""
        <div style="margin-bottom: 15px; padding: 10px; border-radius: 6px; cursor: pointer;
                  background-color: {bg_color}; transition: all 0.2s ease;"
             onmouseover="this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.1)) for j in (0, 2, 4))}, 0.15)'; 
                         this.style.transform='translateX(5px)';"
             onmouseout="this.style.backgroundColor='{bg_color}'; this.style.transform='translateX(0)';"
             onclick="this.style.backgroundColor='rgba({','.join(str(int(int(color.lstrip('#')[j:j+2], 16) * 0.1)) for j in (0, 2, 4))}, 0.3)';
                      parent.postMessage({{highlighted_item: '{name}', comparison_id: '{comparison_id}'}}, '*');">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="margin-right: 8px; font-size: 16px;" title="{tooltip}">{indicator}</div>
                    <div style="font-weight: 500; color: #2c3e50;">{name}</div>
                </div>
                <div style="font-weight: bold; color: {color};">{value}</div>
            </div>
            <div style="position: relative; background-color: #f1f1f1; border-radius: 6px; height: 12px; width: 100%; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; background-color: {color}; height: 100%; width: {percentage}%; 
                            border-radius: 6px; transition: width 0.5s ease-out;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                <div style="font-size: 12px; color: #7f8c8d;">0</div>
                <div style="font-size: 12px; color: #7f8c8d;">{int(max_value)}</div>
            </div>
        </div>
        """
        render_html(bar_html)
        
        # Show detail view if item is highlighted
        if is_highlighted:
            with st.expander(f"Details for {name}", expanded=True):
                # Create a more detailed view with additional metrics
                additional_metrics = {
                    "Percentile": f"{(i / len(sorted_items) * 100):.1f}%",
                    "Relative Strength": f"{(value / sorted_items[0]['value'] * 100):.1f}%" if i > 0 and direction == 'higher_better' else 
                                        f"{(value / sorted_items[-1]['value'] * 100):.1f}%" if i < len(sorted_items) - 1 and direction == 'lower_better' else
                                        "100% (Benchmark)",
                    "Status": "Strong performer" if (direction == "higher_better" and i < len(sorted_items) // 3) or 
                              (direction == "lower_better" and i > 2 * len(sorted_items) // 3) else
                              "Average performer" if (i >= len(sorted_items) // 3 and i <= 2 * len(sorted_items) // 3) else
                              "Needs improvement"
                }
                
                metric_cols = st.columns(3)
                for j, (metric_name, metric_value) in enumerate(additional_metrics.items()):
                    with metric_cols[j]:
                        st.metric(label=metric_name, value=metric_value)
                
                st.markdown(f"""
                #### Recommendation
                
                {
                "Focus on maintaining this strong performance and consider using it as a benchmark for other areas." 
                if (direction == "higher_better" and i < len(sorted_items) // 3) or 
                   (direction == "lower_better" and i > 2 * len(sorted_items) // 3) else
                
                "This area shows average performance. Consider moderate improvements to gain competitive advantage."
                if (i >= len(sorted_items) // 3 and i <= 2 * len(sorted_items) // 3) else
                
                "This area requires attention. Develop strategies to improve performance to competitive levels."
                }
                """)
                
                # Actions for this item
                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button("Generate Improvement Plan", key=f"plan_{name}_{comparison_id}", use_container_width=True):
                        st.info(f"Generating improvement plan for {name}...")
                
                with action_cols[1]:
                    if st.button("Close Details", key=f"close_{name}_{comparison_id}", use_container_width=True):
                        st.session_state[comparison_id]["highlighted_item"] = None
                        st.rerun()  # Updated from deprecated st.experimental_rerun()
    
    # Add a summary section
    with st.expander("Summary & Insights"):
        # Show summary metrics
        top_performer = sorted_items[0]["name"] if direction == "higher_better" else sorted_items[-1]["name"]
        needs_improvement = sorted_items[-1]["name"] if direction == "higher_better" else sorted_items[0]["name"]
        
        st.markdown(f"""
        #### Key Insights
        
        - **Top Performer**: {top_performer} is leading with a value of {sorted_items[0]["value"] if direction == "higher_better" else sorted_items[-1]["value"]}
        - **Needs Improvement**: {needs_improvement} shows the {"lowest" if direction == "higher_better" else "highest"} value at {sorted_items[-1]["value"] if direction == "higher_better" else sorted_items[0]["value"]}
        - **Average Value**: {sum(float(item["value"]) for item in sorted_items) / len(sorted_items):.1f}
        
        #### Recommendations
        
        - Focus resources on improving {needs_improvement} to bring it closer to the average
        - Study the strategies employed by {top_performer} to identify best practices
        - Consider setting benchmarks based on top performers to drive improvement
        """)
        
        # Add action buttons
        if st.button("Generate Comprehensive Report", key=f"report_{comparison_id}", use_container_width=True):
            st.info("Generating comprehensive comparative analysis report...")
            
    return sorted_items

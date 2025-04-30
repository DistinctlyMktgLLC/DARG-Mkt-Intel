import streamlit as st
from streamlit.components.v1 import html

def render_html(html_content, height=None):
    """
    Render HTML content using the proper Streamlit component.
    
    Args:
        html_content (str): The HTML content to render
        height (int, optional): The height of the HTML component in pixels
        
    Returns:
        None: Renders the HTML directly
    """
    html(html_content, height=height)

def render_card(title, content, color="#3498db", height=None):
    """
    Render a card-style UI component with title and content.
    
    Args:
        title (str): The card title
        content (str): The HTML content for the card body
        color (str, optional): The accent color for the card
        height (int, optional): The height of the card in pixels
        
    Returns:
        None: Renders the card directly
    """
    card_html = f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="background-color: {color}; color: white; padding: 10px 15px;">
            <h3 style="margin: 0;">{title}</h3>
        </div>
        <div style="padding: 15px; background-color: white;">
            {content}
        </div>
    </div>
    """
    html(card_html, height=height)

def render_tag(text, type="default", inline=True):
    """
    Render a tag/badge element.
    
    Args:
        text (str): The tag text
        type (str, optional): Tag type (default, success, warning, danger)
        inline (bool, optional): Whether to display inline or block
        
    Returns:
        None: Renders the tag directly
    """
    color_map = {
        "default": "#3498db",
        "success": "#2ecc71",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "info": "#3498db"
    }
    
    color = color_map.get(type, color_map["default"])
    display = "inline-block" if inline else "block"
    
    tag_html = f"""
    <div style="display: {display}; background-color: {color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; margin-bottom: 5px;">
        {text}
    </div>
    """
    html(tag_html)

def render_progress(value, max_value=100, label=None, color="#3498db", height=30):
    """
    Render a custom progress bar.
    
    Args:
        value (float): Current value
        max_value (float, optional): Maximum value
        label (str, optional): Optional label to display
        color (str, optional): Progress bar color
        height (int, optional): Height of the progress bar
        
    Returns:
        None: Renders the progress bar directly
    """
    percentage = min(100, max(0, (value / max_value) * 100))
    
    label_html = f"<div style='margin-bottom: 5px;'>{label}</div>" if label else ""
    
    progress_html = f"""
    {label_html}
    <div style="background-color: #f0f0f0; border-radius: 4px; height: {height}px; width: 100%; overflow: hidden;">
        <div style="background-color: {color}; height: 100%; width: {percentage}%; transition: width 0.5s ease;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 5px;">
        <span>0</span>
        <span>{value} / {max_value}</span>
        <span>{max_value}</span>
    </div>
    """
    html(progress_html)

def render_timeline_item(title, content, connector=True):
    """
    Render a timeline item for step-by-step displays.
    
    Args:
        title (str): The timeline item title
        content (str): The HTML content for the timeline item
        connector (bool, optional): Whether to show connector to next item
        
    Returns:
        None: Renders the timeline item directly
    """
    connector_html = """
    <div style="margin-left: 12px; border-left: 2px solid #e0e0e0; height: 20px;"></div>
    """ if connector else ""
    
    timeline_html = f"""
    <div style="display: flex; margin-bottom: 5px;">
        <div style="display: flex; flex-direction: column; align-items: center; margin-right: 15px;">
            <div style="width: 24px; height: 24px; border-radius: 50%; background-color: #3498db; display: flex; justify-content: center; align-items: center; color: white; font-weight: bold;">
                ✓
            </div>
            {connector_html}
        </div>
        <div style="flex: 1;">
            <h4 style="margin: 0 0 5px 0;">{title}</h4>
            <div style="margin-bottom: 15px;">
                {content}
            </div>
        </div>
    </div>
    """
    html(timeline_html)

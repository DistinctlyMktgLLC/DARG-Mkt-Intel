import os
import streamlit as st
import time
import json
import logging
import datetime
from functools import wraps
from urllib.parse import urlparse
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client - using custom implementation to avoid import errors
def get_supabase_client():
    """Get a Supabase client with proper error handling."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.warning("Missing Supabase credentials (URL or key).")
        return None
    
    try:
        from supabase import create_client, Client
        return create_client(supabase_url, supabase_key)
    except ImportError:
        logger.warning("Supabase Python client not installed.")
        return None
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {str(e)}")
        return None

# Try to get Supabase client
supabase = get_supabase_client()

# Tier definitions with features and limits
TIER_DEFINITIONS = {
    "Free": {
        "level": 0,
        "price": "Free",
        "description": "Basic access to explore market intelligence",
        "data_percentage": 10,
        "features": {
            "market_map": "Limited to 10% of data points",
            "export": False,
            "detailed_analysis": False,
            "api_access": False,
            "support": "Community forum"
        },
        "color": "#3498db",  # Blue
        "icon": "🔹"
    },
    "Accelerate": {
        "level": 1,
        "price": "$49/month",
        "description": "Enhanced access for growing businesses",
        "data_percentage": 50,
        "features": {
            "market_map": "Access to 50% of data points",
            "export": True,
            "detailed_analysis": True,
            "api_access": False,
            "support": "Email support"
        },
        "color": "#f39c12",  # Orange
        "icon": "🔸"
    },
    "Scale": {
        "level": 2,
        "price": "$199/month",
        "description": "Full enterprise access with advanced features",
        "data_percentage": 100,
        "features": {
            "market_map": "Full access to all data points",
            "export": True,
            "detailed_analysis": True,
            "api_access": True,
            "support": "Priority support & training"
        },
        "color": "#27ae60",  # Green
        "icon": "⭐"
    }
}

# Initialize user session info if not present
if 'user_info' not in st.session_state:
    st.session_state.user_info = {
        "tier": "Free",
        "name": "Demo User",
        "email": "demo@example.com",
        "last_active": datetime.datetime.now().isoformat(),
        "feature_usage": {},
        "data_access_count": 0,
        "login_time": datetime.datetime.now().isoformat()
    }

# Function to get user tier with enhanced tracking
def get_user_tier():
    """
    Get the user's current subscription tier with usage tracking.
    
    Returns:
        str: The user's tier (Free, Accelerate, or Scale)
    """
    # For demo/development: Get tier from session state or default to Free
    if "user_info" in st.session_state and "tier" in st.session_state.user_info:
        # Update last active
        st.session_state.user_info["last_active"] = datetime.datetime.now().isoformat()
        return st.session_state.user_info["tier"]
    
    # If we have Supabase, try to get user's tier from auth
    if supabase:
        try:
            # Get current user
            user = supabase.auth.get_user()
            if user and hasattr(user, 'user') and user.user and user.user.id:
                # Get user profile with tier information
                profile = supabase.table("user_profiles").select("tier").eq("id", user.user.id).execute()
                
                if profile.data and len(profile.data) > 0:
                    tier = profile.data[0].get("tier", "Free")
                    
                    # Update user info in session state
                    if "user_info" not in st.session_state:
                        st.session_state.user_info = {}
                    
                    st.session_state.user_info["tier"] = tier
                    st.session_state.user_info["id"] = user.user.id
                    st.session_state.user_info["email"] = user.user.email
                    st.session_state.user_info["last_active"] = datetime.datetime.now().isoformat()
                    
                    # Track login if first time
                    if "login_time" not in st.session_state.user_info:
                        st.session_state.user_info["login_time"] = datetime.datetime.now().isoformat()
                    
                    return tier
        except Exception as e:
            logger.error(f"Error getting user tier from Supabase: {str(e)}")
    
    # Default to Free tier
    return "Free"

def get_tier_percentage():
    """
    Get the percentage of data a user can access based on their tier.
    
    Returns:
        int: The percentage (0-100) of data the user can access
    """
    user_tier = get_user_tier()
    return TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])["data_percentage"]

def set_user_tier(tier):
    """
    Set the user's subscription tier with proper validation and tracking.
    
    Args:
        tier (str): The tier to set (Free, Accelerate, or Scale)
    
    Returns:
        bool: Whether the tier was successfully set
    """
    if tier not in TIER_DEFINITIONS:
        logger.warning(f"Invalid tier specified: {tier}")
        return False
    
    # Update user info in session state
    if "user_info" not in st.session_state:
        st.session_state.user_info = {}
    
    previous_tier = st.session_state.user_info.get("tier", "Free")
    st.session_state.user_info["tier"] = tier
    st.session_state.user_info["tier_change_time"] = datetime.datetime.now().isoformat()
    
    # Track tier changes for analytics
    if "tier_history" not in st.session_state.user_info:
        st.session_state.user_info["tier_history"] = []
    
    st.session_state.user_info["tier_history"].append({
        "from": previous_tier,
        "to": tier,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # Update tier in Supabase if connected
    if supabase and "id" in st.session_state.user_info:
        try:
            user_id = st.session_state.user_info["id"]
            supabase.table("user_profiles").update({"tier": tier}).eq("id", user_id).execute()
            logger.info(f"Updated user {user_id} to tier {tier} in Supabase")
        except Exception as e:
            logger.error(f"Error updating tier in Supabase: {str(e)}")
    
    return True

def track_feature_usage(feature_name):
    """
    Track usage of a specific feature for analytics.
    
    Args:
        feature_name (str): The name of the feature being used
    """
    if "user_info" not in st.session_state:
        st.session_state.user_info = {}
    
    if "feature_usage" not in st.session_state.user_info:
        st.session_state.user_info["feature_usage"] = {}
    
    if feature_name not in st.session_state.user_info["feature_usage"]:
        st.session_state.user_info["feature_usage"][feature_name] = 0
    
    st.session_state.user_info["feature_usage"][feature_name] += 1
    
    # Track data access count for analytics
    if "data_access_count" not in st.session_state.user_info:
        st.session_state.user_info["data_access_count"] = 0
    
    st.session_state.user_info["data_access_count"] += 1

def can_access_feature(feature_name):
    """
    Check if the user's tier allows access to a specific feature.
    
    Args:
        feature_name (str): The name of the feature to check access for
        
    Returns:
        bool: Whether the user can access the feature
    """
    user_tier = get_user_tier()
    tier_info = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])
    
    # Check if feature exists in the tier definition
    if feature_name in tier_info["features"]:
        feature_access = tier_info["features"][feature_name]
        
        # If feature_access is a boolean, return it directly
        if isinstance(feature_access, bool):
            return feature_access
        
        # Otherwise, the feature is available with some limitations
        return True
    
    # Feature not found in definitions, default to False
    return False

def get_feature_limitations(feature_name):
    """
    Get any limitations on a feature for the user's current tier.
    
    Args:
        feature_name (str): The name of the feature to check
        
    Returns:
        str or None: Description of limitations or None if no limitations
    """
    user_tier = get_user_tier()
    tier_info = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])
    
    # Check if feature exists in the tier definition
    if feature_name in tier_info["features"]:
        feature_access = tier_info["features"][feature_name]
        
        # If feature_access is a boolean, there are no limitations to describe
        if isinstance(feature_access, bool):
            return None
        
        # Otherwise, return the limitation description
        return feature_access
    
    # Feature not found in definitions
    return None

def enforce_tier(required_tier):
    """
    Enforce tier-based access control with enhanced UX.
    Redirects to an upgrade page if the user's tier is insufficient.
    
    Args:
        required_tier (str): The tier required to access the feature
        
    Returns:
        bool: True if access is allowed, False otherwise (though it stops execution)
    """
    user_tier = get_user_tier()
    user_level = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])["level"]
    required_level = TIER_DEFINITIONS.get(required_tier, TIER_DEFINITIONS["Free"])["level"]
    
    # Check if user's tier is sufficient
    if user_level < required_level:
        # Create a visually appealing upgrade page
        st.markdown(f"<h1 style='color: {TIER_DEFINITIONS[required_tier]['color']};'>✨ Upgrade to {required_tier}</h1>", unsafe_allow_html=True)
        
        st.warning(f"This feature requires {required_tier} tier access. You currently have {user_tier} tier access.")
        
        # Display tier comparison in columns
        st.markdown("### Compare Plans")
        
        # Create columns for each tier
        cols = st.columns(len(TIER_DEFINITIONS))
        
        # Populate tier information in each column
        for i, (tier_name, tier_data) in enumerate(TIER_DEFINITIONS.items()):
            with cols[i]:
                # Highlight the current tier and required tier
                if tier_name == user_tier:
                    st.markdown(f"<div style='padding: 10px; border-radius: 5px; border: 2px solid {tier_data['color']}; margin-bottom: 15px;'>", unsafe_allow_html=True)
                    st.markdown(f"## {tier_data['icon']} {tier_name}")
                    st.markdown("**Your Current Plan**")
                elif tier_name == required_tier:
                    st.markdown(f"<div style='padding: 10px; border-radius: 5px; border: 2px solid {tier_data['color']}; background-color: rgba({','.join(str(int(c * 255)) for c in hex_to_rgb(tier_data['color']) + (0.1,))});'>", unsafe_allow_html=True)
                    st.markdown(f"## {tier_data['icon']} {tier_name}")
                    st.markdown("**Recommended Plan**")
                else:
                    st.markdown("<div style='padding: 10px; border-radius: 5px; border: 1px solid #ddd;'>", unsafe_allow_html=True)
                    st.markdown(f"## {tier_data['icon']} {tier_name}")
                
                # Display tier details
                st.markdown(f"**{tier_data['price']}**")
                st.markdown(tier_data['description'])
                
                # Display key features as a list
                st.markdown("#### Features:")
                for feature, value in tier_data['features'].items():
                    if isinstance(value, bool):
                        icon = "✅" if value else "❌"
                        st.markdown(f"{icon} {feature.replace('_', ' ').title()}")
                    else:
                        st.markdown(f"✅ {feature.replace('_', ' ').title()}: {value}")
                
                # Add an upgrade button if this is the required tier or higher
                if TIER_DEFINITIONS[tier_name]["level"] >= required_level:
                    if st.button(f"Upgrade to {tier_name}", key=f"upgrade_{tier_name}", use_container_width=True):
                        # In a real application, this would redirect to a payment page
                        st.success(f"Upgrading to {tier_name} tier... (Demo only)")
                        time.sleep(1)
                        
                        # For demo purposes only - upgrade the user
                        set_user_tier(tier_name)
                        st.rerun()  # Updated from deprecated st.experimental_rerun()
                
                # Close the div
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Feature highlight specific to the required tier
        st.markdown(f"### Why Upgrade to {required_tier}?")
        
        # Highlight specific features based on the required tier
        if required_tier == "Accelerate":
            benefits = [
                "**50% more market data** for more comprehensive analysis",
                "**Export capabilities** to integrate with your workflows",
                "**Detailed market analysis** with advanced visualizations",
                "**Email support** for your questions and needs"
            ]
        elif required_tier == "Scale":
            benefits = [
                "**100% complete market data** for full-spectrum insights",
                "**API access** to integrate with your systems",
                "**Priority support and training** for your team",
                "**Advanced analytics features** for deeper intelligence"
            ]
        else:
            benefits = []
        
        # Display the benefits as a bulleted list
        for benefit in benefits:
            st.markdown(f"- {benefit}")
        
        # For demo purposes - add tier switching buttons in an expander
        with st.expander("Demo Controls (For Testing Only)", expanded=False):
            st.markdown("These controls are for demonstration purposes only.")
            
            tier_cols = st.columns(3)
            with tier_cols[0]:
                if st.button("Switch to Free Tier", use_container_width=True):
                    set_user_tier("Free")
                    st.rerun()  # Updated from deprecated st.experimental_rerun()
            with tier_cols[1]:
                if st.button("Switch to Accelerate Tier", use_container_width=True):
                    set_user_tier("Accelerate")
                    st.rerun()  # Updated from deprecated st.experimental_rerun()
            with tier_cols[2]:
                if st.button("Switch to Scale Tier", use_container_width=True):
                    set_user_tier("Scale")
                    st.rerun()  # Updated from deprecated st.experimental_rerun()
            
            # Add a way to view the current user info (anonymized)
            if st.checkbox("View Session Info"):
                # Anonymize some fields for display
                display_info = st.session_state.user_info.copy()
                if "email" in display_info:
                    email_parts = display_info["email"].split("@")
                    if len(email_parts) > 1:
                        display_info["email"] = f"{email_parts[0][:3]}...@{email_parts[1]}"
                
                st.json(display_info)
        
        # Stop execution of the rest of the page
        st.stop()
    
    # Track successful access to tier-restricted feature
    track_feature_usage(f"access_{required_tier}_feature")
    
    return True

def tier_limited(func):
    """
    Decorator for tier-limited functions with usage tracking.
    
    Usage:
        @tier_limited
        def premium_function(required_tier="Scale", *args, **kwargs):
            # Function implementation
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        required_tier = kwargs.pop("required_tier", "Free")
        feature_name = kwargs.pop("feature_name", func.__name__)
        
        # Track attempted usage
        track_feature_usage(f"attempt_{feature_name}")
        
        if enforce_tier(required_tier):
            # Track successful usage
            track_feature_usage(feature_name)
            return func(*args, **kwargs)
        
        # If enforce_tier doesn't stop execution, stop here
        st.stop()
    
    return wrapper

def apply_tier_limit(data, tier_percentage=None):
    """
    Apply tier-based data limitations to a dataset.
    
    Args:
        data: List or DataFrame of data
        tier_percentage (int, optional): Override the tier percentage, otherwise use user's tier
    
    Returns:
        Limited data based on user's tier
    """
    if tier_percentage is None:
        tier_percentage = get_tier_percentage()
    
    if not data:
        return data
    
    # If the tier has full access, return all data
    if tier_percentage >= 100:
        return data
    
    # Handle different data types
    import pandas as pd
    if isinstance(data, pd.DataFrame):
        # For DataFrames, limit by percentage of rows
        limit_size = max(1, int(len(data) * tier_percentage / 100))
        return data.head(limit_size)
    elif isinstance(data, list):
        # For lists, limit by percentage of items
        limit_size = max(1, int(len(data) * tier_percentage / 100))
        return data[:limit_size]
    elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        # For API-style responses with a data field containing a list
        limit_size = max(1, int(len(data["data"]) * tier_percentage / 100))
        data_copy = data.copy()
        data_copy["data"] = data["data"][:limit_size]
        
        # Add a note about tier limitations
        if "meta" not in data_copy:
            data_copy["meta"] = {}
        
        data_copy["meta"]["tier_limited"] = True
        data_copy["meta"]["tier_percentage"] = tier_percentage
        data_copy["meta"]["showing"] = limit_size
        data_copy["meta"]["total"] = len(data["data"])
        
        return data_copy
    
    # For other data types, return as is
    return data

def render_tier_badge(location="sidebar"):
    """
    Render a visual badge showing the user's current tier.
    
    Args:
        location (str): Where to render the badge ('sidebar' or 'main')
    """
    user_tier = get_user_tier()
    tier_info = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])
    
    badge_html = f"""
    <div style="display: inline-flex; align-items: center; 
                background-color: {tier_info['color']}; color: white;
                padding: 5px 10px; border-radius: 20px; margin: 5px 0;">
        <span style="font-size: 1.2em; margin-right: 5px;">{tier_info['icon']}</span>
        <span>{user_tier} Tier</span>
    </div>
    """
    
    if location == "sidebar":
        st.sidebar.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.markdown(badge_html, unsafe_allow_html=True)

def render_upgrade_button(required_tier, button_text=None, container=None):
    """
    Render an upgrade button that only appears if the user needs to upgrade.
    
    Args:
        required_tier (str): The tier required for the feature
        button_text (str, optional): Custom text for the button
        container (streamlit container, optional): Container to render in
    
    Returns:
        bool: Whether the button was clicked
    """
    user_tier = get_user_tier()
    user_level = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])["level"]
    required_level = TIER_DEFINITIONS.get(required_tier, TIER_DEFINITIONS["Free"])["level"]
    
    # Only show the button if an upgrade is needed
    if user_level < required_level:
        button_container = container if container else st
        
        if not button_text:
            button_text = f"Upgrade to {required_tier} Tier"
            
        return button_container.button(
            button_text, 
            key=f"upgrade_to_{required_tier}_{id(container)}", 
            type="primary"
        )
    
    return False

def render_tier_notice(feature_name, required_tier):
    """
    Render a notice about tier limitations for a specific feature.
    
    Args:
        feature_name (str): The name of the feature
        required_tier (str): The tier required for full access
    """
    user_tier = get_user_tier()
    user_level = TIER_DEFINITIONS.get(user_tier, TIER_DEFINITIONS["Free"])["level"]
    required_level = TIER_DEFINITIONS.get(required_tier, TIER_DEFINITIONS["Free"])["level"]
    
    tier_percentage = get_tier_percentage()
    
    if user_level < required_level:
        st.info(f"💡 You're seeing {tier_percentage}% of available data with your {user_tier} tier. Upgrade to {required_tier} tier for full access to {feature_name}.")
    elif user_level == required_level and required_tier != "Scale":
        next_tier = "Scale"
        st.info(f"💡 Want even more insights? Upgrade to {next_tier} tier for 100% data access and additional premium features.")

# Utility functions
def hex_to_rgb(hex_color):
    """Convert hex color to RGB values (0-1 range)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

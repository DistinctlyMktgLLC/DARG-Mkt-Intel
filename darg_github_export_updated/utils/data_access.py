import os
import json
import pandas as pd
import logging
from utils.tier_control import get_user_tier

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data_access")

# Supabase setup - moved to function to avoid immediate connection attempt
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
environment = os.environ.get("ENVIRONMENT", "development")
supabase = None

# Log environment information
logger.info(f"Data access module initialized in {environment} environment")
if not supabase_url or not supabase_key:
    logger.warning("Supabase credentials not found in environment variables")

def clean_lat_lon(data, lat_col='latitude', lon_col='longitude'):
    """
    Ensures latitude and longitude columns are numeric and valid.
    Accepts a list of dicts or a DataFrame.
    Returns a cleaned DataFrame.
    """
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("Input must be a list of dicts or a DataFrame")
    # Convert to numeric, force errors to NaN
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
    # Drop rows with missing or out-of-bounds coordinates
    df = df.dropna(subset=[lat_col, lon_col])
    df = df[(df[lat_col] >= -90) & (df[lat_col] <= 90)]
    df = df[(df[lon_col] >= -180) & (df[lon_col] <= 180)]
    return df

def get_supabase_client():
    """Get a Supabase client, handling connection issues gracefully"""
    global supabase
    if supabase is not None:
        return supabase

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not set in environment variables")
        return None

    try:
        from supabase import create_client, Client
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase")

        # Verify connection with a simple ping only in production
        # Skip this in development (Replit) to avoid DNS issues
        if os.environ.get("ENVIRONMENT") == "production":
            try:
                # Simple query to test the connection
                supabase.table('people_data').select('*').limit(1).execute()
                logger.info("Supabase connection verified with test query")
            except Exception as conn_e:
                logger.warning(f"Connected to Supabase but test query failed: {str(conn_e)}")
                # We still return the client since it might work for other operations

        return supabase
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        return None

# Tier access percentages
TIER_ACCESS = {
    "Free": 33,
    "Accelerate": 66,
    "Scale": 100
}

def get_tier_percentage():
    """Get the percentage of data a user can access based on their tier."""
    tier = get_user_tier()
    return TIER_ACCESS.get(tier, 33)  # Default to Free tier access

def execute_supabase_function(function_name, params=None):
    """
    Execute a SQL function through Supabase RPC with proper error handling.

    Args:
        function_name (str): The name of the SQL function to execute
        params (dict): Parameters to pass to the function

    Returns:
        dict: The result of the function or an error message
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        return {"error": "Supabase client not available"}

    try:
        response = supabase_client.rpc(function_name, params or {}).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return {"error": "No data returned from Supabase function"}
    except Exception as e:
        logger.error(f"Supabase function error ({function_name}): {str(e)}")
        return {"error": str(e)}

def get_map_data(state_filter=None):
    """
    Get map data with proper tier-based filtering and error handling.

    Args:
        state_filter (list): Optional list of state codes to filter by

    Returns:
        dict: Processed map data or error message
    """
    # In production, always attempt to get data from Supabase first
    # Only fall back to sample data if the connection fails

    # Try to get real data from Supabase in production
    tier_percentage = get_tier_percentage()

    # Call Supabase function - trying exact names from your SQL Editor
    result = execute_supabase_function(
        "get_map_data_with_tooltips",
        {
            "tier_percentage": tier_percentage,
            "state_filter": state_filter
        }
    )

    # If that doesn't work, try alternative function names
    if isinstance(result, dict) and "error" in result:
        logger.info("Trying alternative map data function")
        result = execute_supabase_function(
            "get_enhanced_map_data",
            {
                "tier_percentage": tier_percentage,
                "state_filter": state_filter
            }
        )

    # Process the result
    if "error" in result:
        logger.warning(f"Error getting map data: {result['error']}")
        # Use sample data as fallback when API fails
        try:
            from utils.sample_data import get_sample_map_data
            sample_data = get_sample_map_data()

            # Apply state filter if provided
            if state_filter and len(state_filter) > 0:
                filtered_data = [city for city in sample_data["data"] if city["state"] in state_filter]
                sample_data["data"] = filtered_data

            # Apply tier-based filtering
            if tier_percentage < 100:
                # Limit the data based on tier percentage
                limit = int(len(sample_data["data"]) * tier_percentage / 100)
                sample_data["data"] = sample_data["data"][:limit]

            # Clean fallback data before returning
            try:
                df = clean_lat_lon(sample_data["data"])
                logger.info(f"Falling back to sample map data ({len(df)} locations, cleaned)")
                return {"data": df.to_dict(orient="records")}
            except Exception as e:
                logger.error(f"Error cleaning fallback lat/lon: {str(e)}")
                return {"data": sample_data["data"], "error": "Lat/lon cleaning failed"}
        except Exception as e:
            logger.error(f"Error getting sample map data fallback: {str(e)}")
            # Return a default structure that won't break the app
            return {"data": [], "error": result["error"]}

    # Extract the data from the result
    data = result.get("get_map_data_with_tooltips") if "get_map_data_with_tooltips" in result else result

    if isinstance(data, str):
        try:
            # Try to parse JSON string if needed
            data = json.loads(data)
        except:
            pass

    # Clean latitude and longitude before returning
    try:
        df = clean_lat_lon(data)
        # Optionally, print for debugging
        print("Cleaned lat/lon types:", df['latitude'].apply(type).value_counts())
        print("Sample cleaned lat/lon:", df[['latitude', 'longitude']].head())
        # Return as list of dicts for compatibility
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Error cleaning lat/lon: {str(e)}")
        # Fallback: return uncleaned data, but warn
        return {"data": data, "error": "Lat/lon cleaning failed"}

def get_demographic_summary(state_filter=None):
    """
    Get demographic summary with proper tier-based filtering.

    Args:
        state_filter (list): Optional list of state codes to filter by

    Returns:
        dict: Demographic summary data or error message
    """
    tier_percentage = get_tier_percentage()

    # Always try to get real data from Supabase first
    # Call Supabase function - trying exact names from your SQL Editor
    result = execute_supabase_function(
        "get_demographic_summary",
        {
            "tier_percentage": tier_percentage,
            "state_filter": state_filter
        }
    )

    # If that fails, try alternative function name
    if isinstance(result, dict) and "error" in result:
        logger.info("Trying alternative demographic function")
        result = execute_supabase_function(
            "get_demographic_and_psychographic_metrics",
            {
                "tier_percentage": tier_percentage,
                "state_filter": state_filter
            }
        )

    # Process the result
    if "error" in result:
        logger.warning(f"Error getting demographic summary: {result['error']}")
        # Use sample data as fallback when API fails
        try:
            from utils.sample_data import get_sample_demographic_data
            sample_data = get_sample_demographic_data()

            # Apply tier-based filtering
            if tier_percentage < 100 and "summary" in sample_data:
                # Limit segments based on tier percentage
                limit = max(1, int(len(sample_data["summary"]) * tier_percentage / 100))
                sample_data["summary"] = sample_data["summary"][:limit]

            logger.info(f"Falling back to sample demographic data")
            return sample_data
        except Exception as e:
            logger.error(f"Error getting sample demographic data: {str(e)}")
            # Return a minimal structure that won't break the app
            return {"summary": [], "error": result["error"]}

    # Extract the data from the result
    data = result.get("get_demographic_summary") if "get_demographic_summary" in result else result

    if isinstance(data, str):
        try:
            # Try to parse JSON string if needed
            data = json.loads(data)
        except:
            pass

    return data

def get_market_insights(state_filter=None, metric_column="market_size"):
    """
    Get market insights with proper tier-based filtering.

    Args:
        state_filter (list): Optional list of state codes to filter by
        metric_column (str): Which metric to analyze (market_size, growth_rate, etc.)

    Returns:
        dict: Market insights data or error message
    """
    tier_percentage = get_tier_percentage()

    # Always try to get real data from Supabase first
    # Call Supabase function
    result = execute_supabase_function(
        "generate_market_insights",
        {
            "tier_percentage": tier_percentage,
            "state_filter": state_filter,
            "metric_column": metric_column
        }
    )

    # Process the result
    if "error" in result:
        logger.warning(f"Error getting market insights: {result['error']}")
        # Use sample data as fallback when API fails
        try:
            from utils.sample_data import get_sample_market_insights
            sample_data = get_sample_market_insights()

            # Apply tier-based filtering
            if tier_percentage < 100:
                # Limit data based on tier percentage
                if "by_state" in sample_data:
                    limit_states = max(1, int(len(sample_data["by_state"]) * tier_percentage / 100))
                    sample_data["by_state"] = sample_data["by_state"][:limit_states]

                if "by_segment" in sample_data:
                    limit_segments = max(1, int(len(sample_data["by_segment"]) * tier_percentage / 100))
                    sample_data["by_segment"] = sample_data["by_segment"][:limit_segments]

            logger.info(f"Falling back to sample market insights data")
            return sample_data
        except Exception as e:
            logger.error(f"Error getting sample market insights: {str(e)}")
            # Return a minimal structure that won't break the app
            return {"by_state": [], "by_segment": [], "error": result["error"]}

    # Extract the data from the result
    data = result.get("generate_market_insights") if "generate_market_insights" in result else result

    if isinstance(data, str):
        try:
            # Try to parse JSON string if needed
            data = json.loads(data)
        except:
            pass

    return data

def get_region_growth_data():
    """
    Get region growth data for dashboard insights.
    Returns simplified data suitable for dashboard display.
    """
    try:
        insights = get_market_insights(metric_column="growth_rate")

        if isinstance(insights, dict) and "error" in insights:
            logger.warning(f"Using sample data for region growth: {insights.get('error')}")
            # Return sample data when API is unavailable
            return {
                "region_name": "Southwest Region",
                "growth_rate": 24,
                "market_value": 14.2,
                "state_code": "TX",
                "_source": "sample"
            }

        # Extract region with highest growth from the insights
        state_insights = insights.get("by_state", [])
        if state_insights:
            # Sort by avg_value (growth rate) in descending order
            sorted_states = sorted(state_insights, key=lambda x: x.get("avg_value", 0), reverse=True)
            top_state = sorted_states[0]

            # Map the state code to a region name
            state_region_map = {
                "CA": "West Coast", "OR": "Pacific Northwest", "WA": "Pacific Northwest",
                "NY": "Northeast", "MA": "Northeast", "CT": "Northeast",
                "TX": "Southwest", "AZ": "Southwest", "NM": "Southwest",
                "FL": "Southeast", "GA": "Southeast", "NC": "Southeast",
                "IL": "Midwest", "OH": "Midwest", "MI": "Midwest"
            }

            state_code = top_state.get("state", "")
            region_name = state_region_map.get(state_code, "Other Region")

            # Calculate market value based on growth rate (simplified)
            growth_rate = top_state.get("avg_value", 0)
            market_value = growth_rate / 2  # Simplified calculation

            return {
                "region_name": region_name,
                "growth_rate": round(growth_rate, 1),
                "market_value": round(market_value, 1),
                "state_code": state_code,
                "_source": "api"
            }
    except Exception as e:
        logger.error(f"Error getting region growth data: {str(e)}")

    # Default return if anything fails
    return {
        "region_name": "Southwest Region",
        "growth_rate": 24,
        "market_value": 14.2,
        "state_code": "TX",
        "_source": "sample"
    }

def get_top_segments(limit=5):
    """
    Get top performing segments for dashboard insights.
    Returns simplified data suitable for dashboard display.
    """
    try:
        insights = get_market_insights(metric_column="value")

        if isinstance(insights, dict) and "error" in insights:
            logger.warning(f"Using sample data for top segments: {insights.get('error')}")
            # Return sample data when API is unavailable
            return [
                {
                    "segment_name": "Empathetic Dreamers",
                    "conversion_rate": 32,
                    "_source": "sample"
                },
                {
                    "segment_name": "Practical Realists",
                    "conversion_rate": 28.5,
                    "_source": "sample"
                },
                {
                    "segment_name": "Analytical Thinkers",
                    "conversion_rate": 24.2,
                    "_source": "sample"
                },
                {
                    "segment_name": "Community Builders",
                    "conversion_rate": 19.7,
                    "_source": "sample"
                },
                {
                    "segment_name": "Innovation Seekers",
                    "conversion_rate": 18.3,
                    "_source": "sample"
                }
            ][:limit]

        # Extract segments with highest value from the insights
        segment_insights = insights.get("by_segment", [])
        if segment_insights:
            # Sort by avg_value in descending order
            sorted_segments = sorted(segment_insights, key=lambda x: x.get("avg_value", 0), reverse=True)
            top_segments = sorted_segments[:limit]

            # Transform to simplified format for dashboard
            result = []
            for segment in top_segments:
                segment_name = segment.get("segment_name", "Unknown")
                # Calculate conversion rate based on value (simplified)
                avg_value = segment.get("avg_value", 0)
                conversion_rate = min(100, max(1, round(avg_value / 3, 1)))  # Scale to reasonable percentage

                result.append({
                    "segment_name": segment_name,
                    "conversion_rate": conversion_rate,
                    "_source": "api"
                })

            return result
    except Exception as e:
        logger.error(f"Error getting top segments: {str(e)}")

    # Default return if anything fails
    return [
        {
            "segment_name": "Empathetic Dreamers",
            "conversion_rate": 32,
            "_source": "sample"
        }
    ]

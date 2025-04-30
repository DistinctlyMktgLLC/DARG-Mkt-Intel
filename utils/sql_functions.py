import os
import psycopg2
import psycopg2.extras
import json
from supabase import create_client, Client

# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Direct database connection setup
db_url = os.environ.get("DATABASE_URL")

def execute_direct_sql(query, params=None):
    """
    Execute a SQL query directly using psycopg2 with proper error handling.
    
    Args:
        query (str): The SQL query to execute
        params (dict/list/tuple, optional): Parameters for the query
        
    Returns:
        list: List of dictionaries containing query results
    """
    if not db_url:
        return {"error": "Database URL not configured"}
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        return {"error": str(e)}

def execute_function(function_name, params=None):
    """
    Execute a SQL function with fallback between direct connection and Supabase.
    
    Args:
        function_name (str): The name of the SQL function to execute
        params (dict, optional): Parameters to pass to the function
        
    Returns:
        dict: The result of the function or an error message
    """
    # First, try direct SQL connection
    direct_result = execute_direct_sql_function(function_name, params)
    
    # If direct SQL fails and Supabase is available, try Supabase
    if "error" in direct_result and supabase:
        try:
            response = supabase.rpc(function_name, params or {}).execute()
            
            if response.data:
                return response.data[0]
            else:
                return {"error": "No data returned from Supabase"}
        except Exception as e:
            # If both methods fail, return the direct SQL error
            return direct_result
    
    return direct_result

def execute_direct_sql_function(function_name, params=None):
    """
    Execute a SQL function directly with proper error handling.
    
    Args:
        function_name (str): The name of the SQL function to execute
        params (dict): Parameters to pass to the function
        
    Returns:
        dict: The result of the function or an error message
    """
    if not db_url:
        return {"error": "Database URL not configured"}
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Build the function call
        if params:
            param_list = []
            for key, value in params.items():
                if isinstance(value, list):
                    # Handle array parameters
                    if not value:
                        param_list.append("NULL::text[]")
                    else:
                        array_str = "ARRAY["
                        array_items = []
                        for item in value:
                            if isinstance(item, (int, float)):
                                array_items.append(str(item))
                            elif isinstance(item, bool):
                                array_items.append(str(item).lower())
                            else:
                                array_items.append(f"'{item}'")
                        array_str += ", ".join(array_items) + "]"
                        param_list.append(array_str)
                elif value is None:
                    param_list.append("NULL")
                elif isinstance(value, bool):
                    param_list.append(str(value).lower())
                elif isinstance(value, (int, float)):
                    param_list.append(str(value))
                else:
                    # Strings and other types
                    param_list.append(f"'{value}'")
            
            query = f"SELECT * FROM {function_name}({', '.join(param_list)})"
        else:
            query = f"SELECT * FROM {function_name}()"
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result or {}
    except Exception as e:
        return {"error": str(e)}

def fix_sql_functions():
    """
    Apply SQL function fixes from the technical guide.
    This function is for administrative use to fix the database functions.
    
    Returns:
        dict: Status of the fix operations
    """
    if not db_url:
        return {"error": "Database URL not configured"}
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Fix for Map Data Function
        cursor.execute("""
        -- Drop existing function
        DROP FUNCTION IF EXISTS get_map_data_optimized_for_api(integer, text[], boolean);

        -- Create fixed function with proper type casting
        CREATE OR REPLACE FUNCTION get_map_data_optimized_for_api(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL,
          include_tooltips BOOLEAN DEFAULT TRUE
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          result JSONB;
          access_limit INTEGER;
          total_rows INTEGER;
        BEGIN
          -- Get total number of rows 
          SELECT COUNT(*) INTO total_rows FROM people_data;
            
          -- Calculate tier-based row limit
          access_limit := (total_rows * tier_percentage / 100)::INTEGER;
          
          -- Generate map data as JSONB directly in SQL
          WITH filtered_data AS (
            SELECT * FROM people_data
            WHERE (state_filter IS NULL OR state = ANY(state_filter))
            ORDER BY RANDOM()
            LIMIT access_limit
          ),
          
          processed_data AS (
            SELECT 
              neighborhood as city,
              state,
              zip_code,
              -- Safe type casting with REGEX validation
              CASE 
                WHEN latitude ~ '^[0-9\\-]+(\.[0-9]+)?$' THEN latitude::NUMERIC 
                ELSE 0 
              END as latitude,
              CASE 
                WHEN longitude ~ '^[0-9\\-]+(\.[0-9]+)?$' THEN longitude::NUMERIC 
                ELSE 0 
              END as longitude,
              kind_of_person as segment,
              CASE 
                WHEN income ~ '^[0-9]+(\.[0-9]+)?$' THEN income::NUMERIC 
                ELSE 0 
              END as market_size,
              CASE 
                WHEN score ~ '^[0-9]+(\.[0-9]+)?$' THEN score::NUMERIC 
                ELSE 0 
              END as growth_rate,
              CASE 
                WHEN accuracy ~ '^[0-9]+(\.[0-9]+)?$' THEN accuracy::NUMERIC 
                ELSE 0 
              END as accuracy,
              CASE 
                WHEN value ~ '^[0-9]+(\.[0-9]+)?$' THEN value::NUMERIC 
                ELSE 0 
              END as value,
              CASE 
                WHEN city_pop ~ '^[0-9]+(\.[0-9]+)?$' THEN city_pop::INTEGER 
                ELSE 0 
              END as population,
              CASE 
                WHEN include_tooltips THEN 
                  '<div class="tooltip-content">' ||
                  '<h4>' || neighborhood || ', ' || state || '</h4>' ||
                  '<p><b>Profile:</b> ' || COALESCE(kind_of_person, 'N/A') || '</p>' ||
                  '<p><b>Market Size:</b> ' || COALESCE(income, 'N/A') || '</p>' ||
                  '<p><b>Growth Rate:</b> ' || COALESCE(score, 'N/A') || '</p>' ||
                  '<p><b>Population:</b> ' || COALESCE(city_pop::TEXT, 'N/A') || '</p>' ||
                  '</div>'
                ELSE NULL
              END AS tooltip
            FROM filtered_data
          ),
          
          summary_stats AS (
            SELECT 
              COUNT(*) AS total_count,
              -- Using properly casted values for aggregations
              AVG(market_size) AS avg_market_size,
              AVG(growth_rate) AS avg_growth_rate,
              AVG(population) AS avg_population,
              COUNT(DISTINCT state) AS total_states,
              jsonb_agg(DISTINCT state) AS state_list
            FROM processed_data
          )
          
          SELECT jsonb_build_object(
            'data', (SELECT jsonb_agg(to_jsonb(t)) FROM processed_data t),
            'meta', jsonb_build_object(
              'count', (SELECT total_count FROM summary_stats),
              'avg_market_size', (SELECT avg_market_size FROM summary_stats),
              'avg_growth_rate', (SELECT avg_growth_rate FROM summary_stats),
              'avg_population', (SELECT avg_population FROM summary_stats),
              'total_states', (SELECT total_states FROM summary_stats),
              'states', (SELECT state_list FROM summary_stats),
              'tier_percentage', tier_percentage
            )
          ) INTO result;
          
          RETURN result;
        END;
        $$;

        -- Drop existing function to avoid signature conflicts
        DROP FUNCTION IF EXISTS get_map_data_with_tooltips(integer, text[]);

        -- Create alias function with the name the frontend is expecting
        CREATE OR REPLACE FUNCTION get_map_data_with_tooltips(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          -- Simply call our optimized function
          RETURN get_map_data_optimized_for_api(tier_percentage, state_filter, true);
        END;
        $$;
        """)
        
        # Fix for Demographic Summary Function
        cursor.execute("""
        -- Drop existing function
        DROP FUNCTION IF EXISTS get_demographic_summary_for_api(integer, text[]);

        -- Create fixed function with proper type casting and NULL handling
        CREATE OR REPLACE FUNCTION get_demographic_summary_for_api(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          result JSONB;
          access_limit INTEGER;
          total_rows INTEGER;
        BEGIN
          -- Get total number of rows 
          SELECT COUNT(*) INTO total_rows FROM people_data;
            
          -- Calculate tier-based row limit
          access_limit := (total_rows * tier_percentage / 100)::INTEGER;
          
          -- Generate demographic summary directly in SQL
          WITH filtered_data AS (
            SELECT * FROM people_data
            WHERE (state_filter IS NULL OR state = ANY(state_filter))
            ORDER BY RANDOM()
            LIMIT access_limit
          ),
          
          -- Gender distribution
          gender_counts AS (
            SELECT 
              COALESCE(gender, 'Unknown') as gender, 
              COUNT(*) as count,
              (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM filtered_data), 0))::NUMERIC(5,2) as percentage
            FROM filtered_data
            GROUP BY gender
          ),
          
          -- Race distribution
          race_counts AS (
            SELECT 
              COALESCE(race, 'Unknown') as race, 
              COUNT(*) as count,
              (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM filtered_data), 0))::NUMERIC(5,2) as percentage
            FROM filtered_data
            GROUP BY race
          ),
          
          -- Income level distribution
          income_counts AS (
            SELECT 
              COALESCE(income_level, 'Unknown') as income_level, 
              COUNT(*) as count,
              (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM filtered_data), 0))::NUMERIC(5,2) as percentage
            FROM filtered_data
            GROUP BY income_level
          ),
          
          -- Education distribution
          education_counts AS (
            SELECT 
              COALESCE(education, 'Unknown') as education, 
              COUNT(*) as count,
              (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM filtered_data), 0))::NUMERIC(5,2) as percentage
            FROM filtered_data
            GROUP BY education
          ),
          
          -- Segment distribution
          segment_counts AS (
            SELECT 
              COALESCE(distinctly_segment_name, 'Unknown') as segment_name, 
              COUNT(*) as count,
              (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM filtered_data), 0))::NUMERIC(5,2) as percentage
            FROM filtered_data
            GROUP BY distinctly_segment_name
          )
          
          -- Build final summary JSON
          SELECT jsonb_build_object(
            'gender', (SELECT jsonb_object_agg(gender, percentage) FROM gender_counts),
            'race', (SELECT jsonb_object_agg(race, percentage) FROM race_counts),
            'income_level', (SELECT jsonb_object_agg(income_level, percentage) FROM income_counts),
            'education', (SELECT jsonb_object_agg(education, percentage) FROM education_counts),
            'segment', (SELECT jsonb_object_agg(segment_name, percentage) FROM segment_counts),
            'meta', jsonb_build_object(
              'count', access_limit,
              'tier_percentage', tier_percentage,
              'states', state_filter
            )
          ) INTO result;
          
          RETURN result;
        END;
        $$;

        -- Drop existing function to avoid signature conflicts
        DROP FUNCTION IF EXISTS get_demographic_summary(integer, text[]);

        -- Create alias function
        CREATE OR REPLACE FUNCTION get_demographic_summary(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          -- Simply call our optimized function
          RETURN get_demographic_summary_for_api(tier_percentage, state_filter);
        END;
        $$;
        """)
        
        # Fix for Market Insights Function
        cursor.execute("""
        -- Drop existing function
        DROP FUNCTION IF EXISTS generate_market_insights_optimized_for_api(integer, text[], text);

        -- Create fixed function with proper type casting
        CREATE OR REPLACE FUNCTION generate_market_insights_optimized_for_api(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL,
          metric_column TEXT DEFAULT 'market_size'
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          result JSONB;
          access_limit INTEGER;
          total_rows INTEGER;
          valid_metric BOOLEAN;
        BEGIN
          -- Validate metric column
          IF metric_column NOT IN ('market_size', 'growth_rate', 'accuracy', 'value') THEN
            metric_column := 'market_size';
          END IF;
          
          -- Get total number of rows 
          SELECT COUNT(*) INTO total_rows FROM people_data;
            
          -- Calculate tier-based row limit
          access_limit := (total_rows * tier_percentage / 100)::INTEGER;
          
          -- Generate market insights with proper column mapping and type casting
          WITH filtered_data AS (
            SELECT 
              *,
              -- Map metric columns with proper type casting
              CASE 
                WHEN metric_column = 'market_size' AND income ~ '^[0-9]+(\.[0-9]+)?$' THEN income::NUMERIC
                WHEN metric_column = 'growth_rate' AND score ~ '^[0-9]+(\.[0-9]+)?$' THEN score::NUMERIC
                WHEN metric_column = 'accuracy' AND accuracy ~ '^[0-9]+(\.[0-9]+)?$' THEN accuracy::NUMERIC
                WHEN metric_column = 'value' AND value ~ '^[0-9]+(\.[0-9]+)?$' THEN value::NUMERIC
                ELSE 0
              END AS metric_value
            FROM people_data
            WHERE (state_filter IS NULL OR state = ANY(state_filter))
            ORDER BY RANDOM()
            LIMIT access_limit
          ),
          
          -- Calculate insights by state
          state_insights AS (
            SELECT 
              state,
              COUNT(*) as count,
              AVG(metric_value) as avg_value,
              MIN(metric_value) as min_value,
              MAX(metric_value) as max_value,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY metric_value) as median_value
            FROM filtered_data
            GROUP BY state
            ORDER BY avg_value DESC
          ),
          
          -- Calculate insights by segment
          segment_insights AS (
            SELECT 
              COALESCE(distinctly_segment_name, 'Unknown') as segment_name,
              COUNT(*) as count,
              AVG(metric_value) as avg_value,
              MIN(metric_value) as min_value,
              MAX(metric_value) as max_value,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY metric_value) as median_value
            FROM filtered_data
            GROUP BY distinctly_segment_name
            ORDER BY avg_value DESC
          ),
          
          -- Overall statistics
          overall_stats AS (
            SELECT 
              COUNT(*) as total_count,
              AVG(metric_value) as avg_value,
              MIN(metric_value) as min_value,
              MAX(metric_value) as max_value,
              PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY metric_value) as median_value
            FROM filtered_data
          )
          
          -- Build final insights JSON
          SELECT jsonb_build_object(
            'by_state', (SELECT jsonb_agg(to_jsonb(t)) FROM state_insights t),
            'by_segment', (SELECT jsonb_agg(to_jsonb(t)) FROM segment_insights t),
            'overall', (SELECT to_jsonb(t) FROM overall_stats t),
            'meta', jsonb_build_object(
              'count', access_limit,
              'tier_percentage', tier_percentage,
              'states', state_filter,
              'metric', metric_column
            )
          ) INTO result;
          
          RETURN result;
        END;
        $$;

        -- Drop existing function to avoid signature conflicts
        DROP FUNCTION IF EXISTS generate_market_insights(integer, text[], text);

        -- Create alias function
        CREATE OR REPLACE FUNCTION generate_market_insights(
          tier_percentage INTEGER DEFAULT 100,
          state_filter TEXT[] DEFAULT NULL,
          metric_column TEXT DEFAULT 'market_size'
        )
        RETURNS JSONB
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          -- Simply call our optimized function
          RETURN generate_market_insights_optimized_for_api(tier_percentage, state_filter, metric_column);
        END;
        $$;

        -- Grant execute permissions
        GRANT EXECUTE ON FUNCTION public.get_map_data_optimized_for_api(integer, text[], boolean) TO PUBLIC;
        GRANT EXECUTE ON FUNCTION public.get_map_data_with_tooltips(integer, text[]) TO PUBLIC;
        GRANT EXECUTE ON FUNCTION public.get_demographic_summary_for_api(integer, text[]) TO PUBLIC;
        GRANT EXECUTE ON FUNCTION public.get_demographic_summary(integer, text[]) TO PUBLIC;
        GRANT EXECUTE ON FUNCTION public.generate_market_insights_optimized_for_api(integer, text[], text) TO PUBLIC;
        GRANT EXECUTE ON FUNCTION public.generate_market_insights(integer, text[], text) TO PUBLIC;

        -- Refresh the schema cache
        NOTIFY pgrst, 'reload schema';
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "SQL functions fixed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

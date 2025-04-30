"""
Sample data module for development/fallback purposes.
This data is only used when Supabase connection fails or in development mode.
"""

import json
import pandas as pd
import numpy as np
import random

def get_sample_map_data():
    """
    Generate sample map data with realistic values for the US market.
    The data includes geographical and market information for major US cities.
    
    Returns:
        dict: Dictionary with a 'data' key containing a list of city data
    """
    # Major US cities with realistic coordinates and populations
    cities = [
        {"city": "New York", "state": "NY", "latitude": 40.7128, "longitude": -74.0060, "population": 8804190},
        {"city": "Los Angeles", "state": "CA", "latitude": 34.0522, "longitude": -118.2437, "population": 3898747},
        {"city": "Chicago", "state": "IL", "latitude": 41.8781, "longitude": -87.6298, "population": 2746388},
        {"city": "Houston", "state": "TX", "latitude": 29.7604, "longitude": -95.3698, "population": 2304580},
        {"city": "Phoenix", "state": "AZ", "latitude": 33.4484, "longitude": -112.0740, "population": 1608139},
        {"city": "Philadelphia", "state": "PA", "latitude": 39.9526, "longitude": -75.1652, "population": 1603797},
        {"city": "San Antonio", "state": "TX", "latitude": 29.4241, "longitude": -98.4936, "population": 1434625},
        {"city": "San Diego", "state": "CA", "latitude": 32.7157, "longitude": -117.1611, "population": 1386932},
        {"city": "Dallas", "state": "TX", "latitude": 32.7767, "longitude": -96.7970, "population": 1304379},
        {"city": "San Jose", "state": "CA", "latitude": 37.3382, "longitude": -121.8863, "population": 1013240},
        {"city": "Austin", "state": "TX", "latitude": 30.2672, "longitude": -97.7431, "population": 961855},
        {"city": "Jacksonville", "state": "FL", "latitude": 30.3322, "longitude": -81.6557, "population": 911507},
        {"city": "Fort Worth", "state": "TX", "latitude": 32.7555, "longitude": -97.3308, "population": 895008},
        {"city": "Columbus", "state": "OH", "latitude": 39.9612, "longitude": -82.9988, "population": 878553},
        {"city": "Indianapolis", "state": "IN", "latitude": 39.7684, "longitude": -86.1581, "population": 863002},
        {"city": "Charlotte", "state": "NC", "latitude": 35.2271, "longitude": -80.8431, "population": 874579},
        {"city": "San Francisco", "state": "CA", "latitude": 37.7749, "longitude": -122.4194, "population": 873965},
        {"city": "Seattle", "state": "WA", "latitude": 47.6062, "longitude": -122.3321, "population": 737015},
        {"city": "Denver", "state": "CO", "latitude": 39.7392, "longitude": -104.9903, "population": 715522},
        {"city": "Washington", "state": "DC", "latitude": 38.9072, "longitude": -77.0369, "population": 689545},
        {"city": "Boston", "state": "MA", "latitude": 42.3601, "longitude": -71.0589, "population": 675647},
        {"city": "Nashville", "state": "TN", "latitude": 36.1627, "longitude": -86.7816, "population": 689447},
        {"city": "Portland", "state": "OR", "latitude": 45.5051, "longitude": -122.6750, "population": 641162},
        {"city": "Las Vegas", "state": "NV", "latitude": 36.1699, "longitude": -115.1398, "population": 641903},
        {"city": "Detroit", "state": "MI", "latitude": 42.3314, "longitude": -83.0458, "population": 639111},
        {"city": "Atlanta", "state": "GA", "latitude": 33.7490, "longitude": -84.3880, "population": 498715},
        {"city": "Miami", "state": "FL", "latitude": 25.7617, "longitude": -80.1918, "population": 454279},
        {"city": "Minneapolis", "state": "MN", "latitude": 44.9778, "longitude": -93.2650, "population": 420324},
        {"city": "New Orleans", "state": "LA", "latitude": 29.9511, "longitude": -90.0715, "population": 390144},
        {"city": "St. Louis", "state": "MO", "latitude": 38.6270, "longitude": -90.1994, "population": 308174}
    ]
    
    # Add market data for each city based partially on population
    for city in cities:
        # Base market size on population with some variation
        pop_factor = city["population"] / 1000000
        
        # Different regions have different economic strengths
        region_multipliers = {
            "CA": 1.4, "WA": 1.3, "OR": 1.1,  # West Coast tech
            "NY": 1.5, "MA": 1.3, "DC": 1.2,  # Northeast finance
            "TX": 1.2, "CO": 1.1, "AZ": 1.0,  # Southwest energy
            "FL": 0.9, "GA": 0.9, "NC": 1.0,  # Southeast tourism/manufacturing
            "IL": 0.8, "OH": 0.7, "MI": 0.7,  # Midwest manufacturing
            "MN": 0.9, "MO": 0.8, "IN": 0.8,  # Heartland agriculture
            "NV": 1.0, "LA": 0.85, "TN": 0.9  # Other regions
        }
        
        state_multiplier = region_multipliers.get(city["state"], 1.0)
        
        # Calculate market size (in thousands)
        market_size = int(pop_factor * random.uniform(10000, 30000) * state_multiplier)
        
        # Calculate growth rate
        # West Coast and Texas have high growth, Midwest slower
        base_growth = {
            "CA": random.uniform(12, 20), "WA": random.uniform(12, 20), "OR": random.uniform(10, 18),
            "TX": random.uniform(10, 18), "AZ": random.uniform(10, 16), "CO": random.uniform(10, 16),
            "NY": random.uniform(6, 14), "MA": random.uniform(6, 12), "DC": random.uniform(6, 12),
            "FL": random.uniform(8, 16), "GA": random.uniform(6, 14), "NC": random.uniform(6, 12),
            "IL": random.uniform(2, 10), "OH": random.uniform(2, 8), "MI": random.uniform(1, 8),
            "MN": random.uniform(4, 10), "IN": random.uniform(2, 8), "MO": random.uniform(2, 8),
            "NV": random.uniform(8, 14), "LA": random.uniform(2, 10), "TN": random.uniform(6, 12)
        }
        
        growth_rate = base_growth.get(city["state"], random.uniform(5, 12))
        
        # Add belief patterns categories to show correlations
        # These would come from the belief analysis system
        innovator_index = random.uniform(20, 90)
        community_focus = random.uniform(20, 90)
        value_driven = random.uniform(20, 90)
        
        # Cities with high innovation/coastal tend to be higher innovator_index
        if city["state"] in ["CA", "WA", "MA", "NY"]:
            innovator_index = min(95, innovator_index * 1.5)
        
        # Areas with more traditional values tend to have higher community focus
        if city["state"] in ["TX", "GA", "TN", "IN", "OH"]:
            community_focus = min(95, community_focus * 1.3)
        
        # Value-driven index adjusted by region
        if city["state"] in ["AZ", "NV", "FL"]:
            value_driven = min(95, value_driven * 1.2)
        
        # Add all calculated fields
        city["market_size"] = market_size
        city["growth_rate"] = round(growth_rate, 1)
        city["innovator_index"] = int(innovator_index)
        city["community_focus"] = int(community_focus)
        city["value_driven"] = int(value_driven)
        city["disposable_income"] = int(market_size / (city["population"] / 100000))
        
        # Add belief pattern correlation indicators
        if innovator_index > 70:
            city["primary_belief"] = "Innovation-focused"
            city["belief_strength"] = int(innovator_index)
        elif community_focus > 70:
            city["primary_belief"] = "Community-oriented"
            city["belief_strength"] = int(community_focus)
        elif value_driven > 70:
            city["primary_belief"] = "Value-driven"
            city["belief_strength"] = int(value_driven)
        else:
            city["primary_belief"] = "Mixed beliefs"
            city["belief_strength"] = 50
            
        # Add response likelihood based on belief patterns (crucial for prediction)
        city["response_likelihood"] = int(
            (innovator_index * 0.3) + 
            (community_focus * 0.3) + 
            (value_driven * 0.4)
        ) / 3
    
    return {"data": cities}

def get_sample_demographic_data():
    """
    Generate sample demographic data with age, income, education, and beliefs.
    
    Returns:
        dict: Dictionary with demographic summaries by segment
    """
    # Define 5 core audience segments with distinct characteristics
    segments = [
        {
            "segment_name": "Empathetic Dreamers",
            "size_percentage": 24,
            "demographics": {
                "age_primary": "25-34",
                "age_secondary": "35-44",
                "income": "Upper Middle",
                "education": "College Degree",
                "urbanicity": "Urban/Suburban"
            },
            "psychographics": {
                "core_values": "Community, Creativity, Empathy",
                "lifestyle": "Socially conscious, Experience-seeking",
                "pain_points": "Desire for meaning, Work-life balance",
                "decision_drivers": "Social impact, Authentic experiences"
            },
            "beliefs": {
                "guiding_principle": "The world needs more empathy and connection",
                "outlook": "Cautiously optimistic",
                "response_to_challenges": "Seek collaborative solutions",
                "priorities": "Experiences over possessions, Social bonds"
            },
            "behaviors": {
                "media_consumption": "Podcasts, Streaming, Social Media (Instagram, TikTok)",
                "purchasing_patterns": "Values-driven, Research-intensive",
                "brand_relationship": "Loyal to aligned brands",
                "content_preferences": "Stories that highlight human connection"
            },
            "conversion_rate": 32,
            "lifetime_value": 84500,
            "mapping": {
                "top_states": ["CA", "NY", "WA", "MA", "CO"],
                "urbanicity": 85  # 0-100 scale, higher = more urban
            }
        },
        {
            "segment_name": "Practical Realists",
            "size_percentage": 21,
            "demographics": {
                "age_primary": "35-44",
                "age_secondary": "45-54",
                "income": "Middle to Upper Middle",
                "education": "College Degree",
                "urbanicity": "Suburban"
            },
            "psychographics": {
                "core_values": "Stability, Quality, Efficiency",
                "lifestyle": "Structured, Goal-oriented",
                "pain_points": "Time constraints, Decision fatigue",
                "decision_drivers": "Value for money, Proven solutions"
            },
            "beliefs": {
                "guiding_principle": "Make smart choices based on evidence and results",
                "outlook": "Pragmatic",
                "response_to_challenges": "Research and plan systematically",
                "priorities": "Financial security, Family stability"
            },
            "behaviors": {
                "media_consumption": "News sites, YouTube how-to content, LinkedIn",
                "purchasing_patterns": "Research-driven, Value-focused",
                "brand_relationship": "Loyal to brands that deliver consistency",
                "content_preferences": "Clear, factual information and demonstrations"
            },
            "conversion_rate": 28.5,
            "lifetime_value": 92700,
            "mapping": {
                "top_states": ["IL", "PA", "TX", "OH", "MN"],
                "urbanicity": 65  # 0-100 scale, higher = more urban
            }
        },
        {
            "segment_name": "Analytical Thinkers",
            "size_percentage": 18,
            "demographics": {
                "age_primary": "35-44",
                "age_secondary": "25-34",
                "income": "Upper Middle to High",
                "education": "Advanced Degree",
                "urbanicity": "Urban"
            },
            "psychographics": {
                "core_values": "Intelligence, Innovation, Efficiency",
                "lifestyle": "Intellectually curious, Tech-savvy",
                "pain_points": "Inefficiency, Lack of depth",
                "decision_drivers": "Logic, Performance, Data"
            },
            "beliefs": {
                "guiding_principle": "Knowledge and optimization lead to progress",
                "outlook": "Forward-thinking",
                "response_to_challenges": "Analyze data and optimize approach",
                "priorities": "Continuous learning, Technological advancement"
            },
            "behaviors": {
                "media_consumption": "Specialized publications, Podcasts, Reddit, Twitter",
                "purchasing_patterns": "Feature-driven, Early adopter",
                "brand_relationship": "Loyal to innovative brands with superior performance",
                "content_preferences": "Detailed specifications, Comparative analyses"
            },
            "conversion_rate": 24.2,
            "lifetime_value": 78800,
            "mapping": {
                "top_states": ["CA", "MA", "WA", "NY", "CO"],
                "urbanicity": 80  # 0-100 scale, higher = more urban
            }
        },
        {
            "segment_name": "Community Builders",
            "size_percentage": 16,
            "demographics": {
                "age_primary": "45-54",
                "age_secondary": "35-44",
                "income": "Middle",
                "education": "Mixed",
                "urbanicity": "Suburban/Rural"
            },
            "psychographics": {
                "core_values": "Tradition, Community, Reliability",
                "lifestyle": "Family-oriented, Local community involvement",
                "pain_points": "Social disconnection, Loss of tradition",
                "decision_drivers": "Trust, Relationships, Community impact"
            },
            "beliefs": {
                "guiding_principle": "Strong communities create a better society",
                "outlook": "Preservation-minded",
                "response_to_challenges": "Rely on trusted networks and proven approaches",
                "priorities": "Family security, Local prosperity"
            },
            "behaviors": {
                "media_consumption": "Local news, Facebook, Cable TV",
                "purchasing_patterns": "Loyalty-driven, Word-of-mouth influence",
                "brand_relationship": "Strong loyalty to trusted community brands",
                "content_preferences": "Stories of local impact and community success"
            },
            "conversion_rate": 19.7,
            "lifetime_value": 67200,
            "mapping": {
                "top_states": ["TX", "OH", "PA", "MI", "NC"],
                "urbanicity": 45  # 0-100 scale, higher = more urban
            }
        },
        {
            "segment_name": "Innovation Seekers",
            "size_percentage": 14,
            "demographics": {
                "age_primary": "25-34",
                "age_secondary": "18-24",
                "income": "Variable",
                "education": "College Degree",
                "urbanicity": "Urban"
            },
            "psychographics": {
                "core_values": "Novelty, Freedom, Self-expression",
                "lifestyle": "Trend-conscious, Digital-first",
                "pain_points": "FOMO, Keeping up with rapid change",
                "decision_drivers": "Uniqueness, Early adoption, Status"
            },
            "beliefs": {
                "guiding_principle": "Embrace change and stand out from the crowd",
                "outlook": "Trendsetting",
                "response_to_challenges": "Seek novel solutions and unique approaches",
                "priorities": "Personal brand, Cultural relevance"
            },
            "behaviors": {
                "media_consumption": "TikTok, Instagram, Twitter, Streaming",
                "purchasing_patterns": "Trend-driven, Early adopter",
                "brand_relationship": "Quick to try new brands, Low loyalty",
                "content_preferences": "Visual, short-form, trending content"
            },
            "conversion_rate": 18.3,
            "lifetime_value": 54800,
            "mapping": {
                "top_states": ["NY", "CA", "FL", "TX", "IL"],
                "urbanicity": 90  # 0-100 scale, higher = more urban
            }
        }
    ]
    
    # Add belief strength correlations
    for segment in segments:
        if segment["segment_name"] == "Empathetic Dreamers":
            segment["belief_correlations"] = {
                "collective_welfare": 85,
                "environmental_concern": 78,
                "fairness_sensitivity": 81,
                "openness_to_experience": 74,
                "need_for_meaning": 89
            }
        elif segment["segment_name"] == "Practical Realists":
            segment["belief_correlations"] = {
                "need_for_stability": 84,
                "value_sensitivity": 76,
                "rationality_preference": 79,
                "risk_aversion": 72,
                "self_reliance": 77
            }
        elif segment["segment_name"] == "Analytical Thinkers":
            segment["belief_correlations"] = {
                "need_for_cognition": 86,
                "efficiency_orientation": 82,
                "rationality_preference": 91,
                "openness_to_experience": 75,
                "technological_enthusiasm": 83
            }
        elif segment["segment_name"] == "Community Builders":
            segment["belief_correlations"] = {
                "tradition_orientation": 88,
                "ingroup_loyalty": 85,
                "local_identity": 90,
                "stability_preference": 79,
                "reciprocity_expectation": 82
            }
        elif segment["segment_name"] == "Innovation Seekers":
            segment["belief_correlations"] = {
                "novelty_seeking": 87,
                "uniqueness_preference": 84,
                "status_consciousness": 76,
                "openness_to_experience": 91,
                "present_orientation": 79
            }
    
    return {"summary": segments}

def get_sample_market_insights():
    """
    Generate sample market insights by state and segment.
    
    Returns:
        dict: Dictionary with insights by state and segment
    """
    # Sample insights by state
    states = [
        {"state": "CA", "state_name": "California", "avg_value": 52500, "growth_rate": 18.4, "market_share": 14.2},
        {"state": "TX", "state_name": "Texas", "avg_value": 48700, "growth_rate": 15.2, "market_share": 12.8},
        {"state": "NY", "state_name": "New York", "avg_value": 54200, "growth_rate": 10.7, "market_share": 11.5},
        {"state": "FL", "state_name": "Florida", "avg_value": 42300, "growth_rate": 14.8, "market_share": 9.7},
        {"state": "IL", "state_name": "Illinois", "avg_value": 43800, "growth_rate": 7.2, "market_share": 6.4},
        {"state": "PA", "state_name": "Pennsylvania", "avg_value": 41200, "growth_rate": 6.8, "market_share": 5.9},
        {"state": "OH", "state_name": "Ohio", "avg_value": 38400, "growth_rate": 5.6, "market_share": 5.1},
        {"state": "GA", "state_name": "Georgia", "avg_value": 40700, "growth_rate": 12.4, "market_share": 4.8},
        {"state": "NC", "state_name": "North Carolina", "avg_value": 39600, "growth_rate": 13.2, "market_share": 4.6},
        {"state": "MI", "state_name": "Michigan", "avg_value": 36800, "growth_rate": 5.4, "market_share": 4.2}
    ]
    
    # Add belief pattern correlations to states
    for state in states:
        # Regional belief patterns
        if state["state"] in ["CA", "WA", "OR"]:  # West Coast
            state["belief_patterns"] = {
                "innovation_focus": random.uniform(70, 90),
                "environmental_concern": random.uniform(75, 90),
                "openness_to_change": random.uniform(70, 85)
            }
        elif state["state"] in ["NY", "MA", "CT"]:  # Northeast
            state["belief_patterns"] = {
                "efficiency_orientation": random.uniform(70, 85),
                "achievement_focus": random.uniform(75, 90),
                "intellectual_focus": random.uniform(70, 85)
            }
        elif state["state"] in ["TX", "AZ", "OK"]:  # Southwest
            state["belief_patterns"] = {
                "independence_value": random.uniform(75, 90),
                "tradition_orientation": random.uniform(65, 80),
                "self_reliance": random.uniform(70, 85)
            }
        elif state["state"] in ["GA", "FL", "SC", "NC"]:  # Southeast
            state["belief_patterns"] = {
                "community_focus": random.uniform(70, 85),
                "tradition_orientation": random.uniform(70, 85),
                "relationship_value": random.uniform(65, 80)
            }
        elif state["state"] in ["IL", "OH", "MI", "IN"]:  # Midwest
            state["belief_patterns"] = {
                "stability_preference": random.uniform(70, 85),
                "work_ethic_value": random.uniform(75, 90),
                "community_focus": random.uniform(65, 80)
            }
        else:  # Default
            state["belief_patterns"] = {
                "stability_preference": random.uniform(60, 80),
                "community_focus": random.uniform(60, 80),
                "openness_to_change": random.uniform(50, 70)
            }
    
    # Sample insights by segment
    segments = [
        {"segment_name": "Empathetic Dreamers", "avg_value": 46700, "growth_rate": 24.2, "conversion_rate": 32.1},
        {"segment_name": "Practical Realists", "avg_value": 51200, "growth_rate": 15.8, "conversion_rate": 28.5},
        {"segment_name": "Analytical Thinkers", "avg_value": 43800, "growth_rate": 18.6, "conversion_rate": 24.2},
        {"segment_name": "Community Builders", "avg_value": 37200, "growth_rate": 10.4, "conversion_rate": 19.7},
        {"segment_name": "Innovation Seekers", "avg_value": 30500, "growth_rate": 22.5, "conversion_rate": 18.3}
    ]
    
    return {
        "by_state": states,
        "by_segment": segments
    }
import streamlit as st
import os
import json
import socket
import time
import subprocess
import requests
import logging
from datetime import datetime
from urllib.parse import urlparse
import pandas as pd
import plotly.graph_objects as go
from utils.tier_control import enforce_tier, get_user_tier
from utils.html_render import render_html, render_card, render_progress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Connection Status | DARG Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce tier access - This page is for admins
enforce_tier('Scale')

# Set session state for history tracking
if 'test_history' not in st.session_state:
    st.session_state.test_history = []

if 'last_test_time' not in st.session_state:
    st.session_state.last_test_time = None

# Title and description
st.title("Supabase Connection Status")
st.write("This diagnostic tool verifies your Supabase connection and troubleshoots common issues.")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Connection Tests", "Advanced Diagnostics", "History", "Deployment Guide"])

def check_environment():
    """Check if required environment variables are set"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    missing_vars = []
    if not supabase_url:
        missing_vars.append("SUPABASE_URL")
        
    if not supabase_key:
        missing_vars.append("SUPABASE_KEY")
    
    if missing_vars:
        return False, f"Missing environment variables: {', '.join(missing_vars)}"
    
    # Check if URL is well-formed
    try:
        parsed_url = urlparse(supabase_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return False, f"SUPABASE_URL is not a valid URL: {supabase_url}"
        
        # Mask the key for security
        masked_key = supabase_key[:4] + "*" * (len(supabase_key) - 8) + supabase_key[-4:] if len(supabase_key) > 8 else "****"
        
        return True, f"Environment variables are properly set. URL domain: {parsed_url.netloc}, API Key: {masked_key}"
    except Exception as e:
        return False, f"Error parsing SUPABASE_URL: {str(e)}"

def check_dns(hostname):
    """Check if the hostname can be resolved using multiple methods"""
    results = []
    success = False
    ip_address = None
    
    # Method 1: Python's socket module
    try:
        ip_address = socket.gethostbyname(hostname)
        success = True
        results.append(f"System DNS resolution successful: {hostname} → {ip_address}")
    except socket.gaierror as e:
        results.append(f"System DNS resolution failed: {str(e)}")
    
    # Method 2: Dig command (if available)
    try:
        dig_result = subprocess.run(
            ["dig", "+short", hostname], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if dig_result.returncode == 0 and dig_result.stdout.strip():
            success = True
            results.append(f"Dig resolution successful: {hostname} → {dig_result.stdout.strip()}")
        else:
            results.append("Dig resolution failed or returned no results")
    except (subprocess.SubprocessError, FileNotFoundError):
        results.append("Dig command not available or failed")
    
    # Method 3: Public DNS resolvers
    try:
        host_cmd = ["host", hostname, "8.8.8.8"]
        host_result = subprocess.run(host_cmd, capture_output=True, text=True, timeout=5)
        
        if host_result.returncode == 0 and "has address" in host_result.stdout:
            public_ip = host_result.stdout.split("has address ")[1].strip()
            success = True
            results.append(f"Google DNS resolution successful: {hostname} → {public_ip}")
        else:
            results.append(f"Google DNS resolution failed: {host_result.stdout.strip()}")
    except (subprocess.SubprocessError, FileNotFoundError):
        results.append("Host command not available or failed")
    
    # Return overall result
    if success:
        return True, "\n".join(results)
    else:
        return False, "\n".join(results)

def check_http_connection(url):
    """Check HTTP connection with detailed information"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed_time = time.time() - start_time
        
        status_code = response.status_code
        if 200 <= status_code < 300:
            return True, f"HTTP connection successful: Status {status_code} in {elapsed_time:.2f}s"
        else:
            return False, f"HTTP connection returned status {status_code} in {elapsed_time:.2f}s - Response: {response.text[:100]}..."
    except requests.exceptions.RequestException as e:
        return False, f"HTTP connection failed: {type(e).__name__}: {str(e)}"

def test_rest_api():
    """Test Supabase REST API directly with comprehensive checks"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        return False, "Cannot test REST API without SUPABASE_URL and SUPABASE_KEY"
    
    # Make sure the URL ends with /rest/v1
    api_url = supabase_url
    if not api_url.endswith('/rest/v1'):
        api_url = f"{api_url.rstrip('/')}/rest/v1"
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        # Try to list the schema information which should work regardless of tables
        start_time = time.time()
        response = requests.get(f"{api_url}/", headers=headers, timeout=10)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            # Try to parse the response as JSON
            try:
                data = response.json()
                tables = list(data.keys()) if isinstance(data, dict) else []
                num_tables = len(tables)
                
                table_list = ", ".join(tables[:5])
                if num_tables > 5:
                    table_list += f" and {num_tables - 5} more"
                    
                return True, f"REST API successful in {elapsed_time:.2f}s. Found {num_tables} tables/views: {table_list}"
            except json.JSONDecodeError:
                return True, f"REST API successful but returned non-JSON response in {elapsed_time:.2f}s"
        else:
            return False, f"REST API failed with status {response.status_code} in {elapsed_time:.2f}s - Response: {response.text[:100]}..."
    except requests.exceptions.RequestException as e:
        return False, f"REST API error: {type(e).__name__}: {str(e)}"

def test_functions_api():
    """Test Supabase Functions API"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        return False, "Cannot test Functions API without SUPABASE_URL and SUPABASE_KEY"
    
    # Make sure the URL ends with /rest/v1/rpc
    api_url = supabase_url
    if not api_url.endswith('/rest/v1/rpc'):
        api_url = f"{api_url.rstrip('/')}/rest/v1/rpc"
    
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Try to call a known function - get_map_data_with_tooltips
        function_data = {
            "tier_percentage": 20,
            "state_filter": ["CA", "NY"]
        }
        
        start_time = time.time()
        response = requests.post(
            f"{api_url}/get_map_data_with_tooltips", 
            headers=headers,
            json=function_data,
            timeout=10
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            return True, f"Function API test successful in {elapsed_time:.2f}s"
        else:
            error_msg = response.text[:100] + "..." if len(response.text) > 100 else response.text
            return False, f"Function API test failed with status {response.status_code} in {elapsed_time:.2f}s - Error: {error_msg}"
    except requests.exceptions.RequestException as e:
        return False, f"Function API test error: {type(e).__name__}: {str(e)}"

def traceroute(hostname, max_hops=15):
    """Perform a traceroute-like test to diagnose connection path issues"""
    results = []
    
    try:
        # Check if traceroute command is available
        traceroute_cmd = ["traceroute", "-m", str(max_hops), "-q", "1", hostname]
        traceroute_result = subprocess.run(traceroute_cmd, capture_output=True, text=True, timeout=20)
        
        if traceroute_result.returncode == 0:
            # Process the traceroute output
            lines = traceroute_result.stdout.strip().split('\n')[1:]  # Skip the header line
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    hop_num = parts[0]
                    host = parts[1]
                    
                    # Look for timing information
                    timing = "timeout"
                    for part in parts[2:]:
                        if "ms" in part:
                            timing = part
                            break
                    
                    results.append(f"Hop {hop_num}: {host} ({timing})")
        else:
            results.append(f"Traceroute command failed: {traceroute_result.stderr}")
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # Try ping as alternative
            ping_cmd = ["ping", "-c", "3", hostname]
            ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
            
            if ping_result.returncode == 0:
                results.append(f"Ping successful: {hostname}")
                ping_lines = ping_result.stdout.strip().split('\n')
                for line in ping_lines[-2:]:  # Get the summary lines
                    results.append(line)
            else:
                results.append(f"Ping failed: {ping_result.stderr}")
        except (subprocess.SubprocessError, FileNotFoundError):
            results.append("Unable to perform network path analysis - traceroute and ping not available")
    
    return results

def test_sql_functions():
    """Test specific SQL functions needed by the application"""
    functions_to_test = [
        "get_map_data_with_tooltips",
        "get_demographic_summary",
        "generate_market_insights"
    ]
    
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        return False, "Cannot test SQL functions without SUPABASE_URL and SUPABASE_KEY"
    
    # Make sure the URL ends with /rest/v1/rpc
    api_url = supabase_url
    if not api_url.endswith('/rest/v1/rpc'):
        api_url = f"{api_url.rstrip('/')}/rest/v1/rpc"
    
    results = []
    all_success = True
    
    for function_name in functions_to_test:
        try:
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple parameters for testing
            function_data = {
                "tier_percentage": 10,
                "state_filter": ["CA"]
            }
            
            if function_name == "generate_market_insights":
                function_data["metric_column"] = "market_size"
            
            start_time = time.time()
            response = requests.post(
                f"{api_url}/{function_name}", 
                headers=headers,
                json=function_data,
                timeout=15
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    data_size = len(json.dumps(data))
                    results.append(f"✅ {function_name}: Success in {elapsed_time:.2f}s ({data_size} bytes)")
                except json.JSONDecodeError:
                    all_success = False
                    results.append(f"❌ {function_name}: Invalid JSON response in {elapsed_time:.2f}s")
            else:
                all_success = False
                error_msg = response.text[:50] + "..." if len(response.text) > 50 else response.text
                results.append(f"❌ {function_name}: Failed with status {response.status_code} in {elapsed_time:.2f}s - {error_msg}")
        except requests.exceptions.RequestException as e:
            all_success = False
            results.append(f"❌ {function_name}: Error {type(e).__name__}: {str(e)}")
    
    return all_success, "\n".join(results)

def run_all_tests():
    """Run all connectivity tests and return the results"""
    results = []
    start_time = time.time()
    
    # Record the test time
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.last_test_time = test_time
    
    # Check environment
    env_ok, env_message = check_environment()
    results.append({
        "test": "Environment Check",
        "status": "✅ Passed" if env_ok else "❌ Failed",
        "message": env_message,
        "timestamp": test_time
    })
    
    if not env_ok:
        df = pd.DataFrame(results)
        # Add to history
        st.session_state.test_history.append({
            "timestamp": test_time,
            "results": df,
            "duration": time.time() - start_time,
            "all_passed": False
        })
        return df
    
    # Parse URL for further tests
    supabase_url = os.environ.get('SUPABASE_URL')
    parsed_url = urlparse(supabase_url)
    hostname = parsed_url.netloc
    
    # Check DNS
    dns_ok, dns_message = check_dns(hostname)
    results.append({
        "test": "DNS Resolution",
        "status": "✅ Passed" if dns_ok else "❌ Failed",
        "message": dns_message,
        "timestamp": test_time
    })
    
    if not dns_ok:
        results.append({
            "test": "HTTP Connection",
            "status": "⚠️ Skipped",
            "message": "DNS check failed, cannot proceed with HTTP tests",
            "timestamp": test_time
        })
        results.append({
            "test": "REST API Test",
            "status": "⚠️ Skipped",
            "message": "DNS check failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        results.append({
            "test": "Functions API Test",
            "status": "⚠️ Skipped",
            "message": "DNS check failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        results.append({
            "test": "SQL Functions Test",
            "status": "⚠️ Skipped",
            "message": "DNS check failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        
        df = pd.DataFrame(results)
        # Add to history
        st.session_state.test_history.append({
            "timestamp": test_time,
            "results": df,
            "duration": time.time() - start_time,
            "all_passed": False
        })
        return df
    
    # Check HTTP
    http_ok, http_message = check_http_connection(supabase_url)
    results.append({
        "test": "HTTP Connection",
        "status": "✅ Passed" if http_ok else "❌ Failed",
        "message": http_message,
        "timestamp": test_time
    })
    
    if not http_ok:
        results.append({
            "test": "REST API Test",
            "status": "⚠️ Skipped",
            "message": "HTTP connection failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        results.append({
            "test": "Functions API Test",
            "status": "⚠️ Skipped",
            "message": "HTTP connection failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        results.append({
            "test": "SQL Functions Test",
            "status": "⚠️ Skipped",
            "message": "HTTP connection failed, cannot proceed with API tests",
            "timestamp": test_time
        })
        
        df = pd.DataFrame(results)
        # Add to history
        st.session_state.test_history.append({
            "timestamp": test_time,
            "results": df,
            "duration": time.time() - start_time,
            "all_passed": False
        })
        return df
    
    # Test REST API
    rest_ok, rest_message = test_rest_api()
    results.append({
        "test": "REST API Test",
        "status": "✅ Passed" if rest_ok else "❌ Failed",
        "message": rest_message,
        "timestamp": test_time
    })
    
    # Test Functions API
    functions_ok, functions_message = test_functions_api()
    results.append({
        "test": "Functions API Test",
        "status": "✅ Passed" if functions_ok else "❌ Failed",
        "message": functions_message,
        "timestamp": test_time
    })
    
    # Test SQL Functions
    sql_ok, sql_message = test_sql_functions()
    results.append({
        "test": "SQL Functions Test",
        "status": "✅ Passed" if sql_ok else "❌ Failed",
        "message": sql_message,
        "timestamp": test_time
    })
    
    df = pd.DataFrame(results)
    
    # All tests passed?
    all_passed = "❌ Failed" not in df["status"].values
    
    # Add to history
    st.session_state.test_history.append({
        "timestamp": test_time,
        "results": df,
        "duration": time.time() - start_time,
        "all_passed": all_passed
    })
    
    return df

def create_health_gauge(success_percentage):
    """Create a gauge chart for connection health"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = success_percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Connection Health"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "red"},
                {'range': [33, 66], 'color': "orange"},
                {'range': [66, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# Main content in Tab 1: Connection Tests
with tab1:
    # Interactive test control
    st.markdown("## Connection Diagnostics")
    
    if st.button("Run Connection Tests", key="run_tests", type="primary"):
        with st.spinner("Running comprehensive connection tests..."):
            test_results = run_all_tests()
            
            # Calculate health score
            total_tests = len(test_results)
            skipped_tests = sum(test_results["status"] == "⚠️ Skipped")
            passed_tests = sum(test_results["status"] == "✅ Passed")
            actual_tests = total_tests - skipped_tests
            
            if actual_tests > 0:
                health_score = int((passed_tests / actual_tests) * 100)
            else:
                health_score = 0
            
            # Display health gauge
            st.plotly_chart(create_health_gauge(health_score))
            
            # Display results
            st.markdown("### Test Results")
            st.dataframe(test_results[["test", "status", "message"]], use_container_width=True)
            
            # Summary
            if "❌ Failed" not in test_results["status"].values:
                st.success("✅ All tests passed successfully! Your Supabase connection is working properly.")
            else:
                st.error(f"❌ {sum(test_results['status'] == '❌ Failed')} of {actual_tests} tests failed. See recommendations below.")
                
                # Add visual timeline of test steps
                status_colors = {
                    "✅ Passed": "#28a745",  # Green
                    "❌ Failed": "#dc3545",  # Red
                    "⚠️ Skipped": "#ffc107"  # Yellow
                }
                
                st.markdown("### Test Flow")
                for i, row in test_results.iterrows():
                    color = status_colors.get(row["status"], "#6c757d")
                    icon = "✓" if row["status"] == "✅ Passed" else "✗" if row["status"] == "❌ Failed" else "⚠"
                    
                    html = f"""
                    <div style="display: flex; margin-bottom: 10px;">
                        <div style="background-color: {color}; color: white; width: 30px; height: 30px; border-radius: 15px; display: flex; justify-content: center; align-items: center; margin-right: 10px;">{icon}</div>
                        <div style="flex-grow: 1;">
                            <div style="font-weight: bold;">{row['test']}</div>
                            <div style="font-size: 0.9em; color: #666;">{row['status']}</div>
                        </div>
                    </div>
                    """
                    render_html(html)
    else:
        # Show last results if available
        if st.session_state.last_test_time:
            st.info(f"Last test was run at {st.session_state.last_test_time}. Press the button above to run again.")
            
            # Find the last test results
            if st.session_state.test_history:
                last_test = st.session_state.test_history[-1]
                test_results = last_test["results"]
                
                # Calculate health score
                total_tests = len(test_results)
                skipped_tests = sum(test_results["status"] == "⚠️ Skipped")
                passed_tests = sum(test_results["status"] == "✅ Passed")
                actual_tests = total_tests - skipped_tests
                
                if actual_tests > 0:
                    health_score = int((passed_tests / actual_tests) * 100)
                else:
                    health_score = 0
                
                # Display health gauge
                st.plotly_chart(create_health_gauge(health_score))
                
                # Display results
                st.markdown("### Previous Test Results")
                st.dataframe(test_results[["test", "status", "message"]], use_container_width=True)
        else:
            st.markdown("""
            ### Welcome to the Connection Diagnostics Tool
            
            This tool helps you identify and troubleshoot connection issues between this application and Supabase.
            
            Click the "Run Connection Tests" button above to start the diagnostic process.
            
            #### What will be tested:
            
            1. **Environment Variables** - Checks if required API keys and URLs are set
            2. **DNS Resolution** - Checks if the Supabase domain can be resolved
            3. **HTTP Connection** - Tests basic connectivity to Supabase endpoints
            4. **REST API** - Verifies that the Supabase REST API is accessible
            5. **Functions API** - Tests RPC function calls that the application relies on
            6. **SQL Functions** - Verifies that specific database functions work correctly
            """)
    
    # Show recommendations based on results
    if 'test_results' in locals() and "❌ Failed" in test_results["status"].values:
        st.markdown("---")
        st.markdown("## Troubleshooting Recommendations")
        
        # Show specific recommendations based on which tests failed
        failed_tests = test_results[test_results["status"] == "❌ Failed"]["test"].tolist()
        
        recommendations = []
        
        if "Environment Check" in failed_tests:
            recommendations.append({
                "title": "Fix Environment Variables",
                "content": """
                ### Missing Environment Variables
                
                Your application needs the following environment variables to connect to Supabase:
                
                - `SUPABASE_URL`: Your Supabase project URL
                - `SUPABASE_KEY`: Your Supabase API key (service role key)
                
                #### How to set environment variables:
                
                **In Local Development:**
                Create a `.streamlit/secrets.toml` file with:
                ```toml
                SUPABASE_URL = "https://your-project-id.supabase.co"
                SUPABASE_KEY = "your-supabase-key"
                ```
                
                **In Replit:**
                1. Go to the "Secrets" tab in the left sidebar
                2. Add each variable with its proper value
                
                **In Streamlit Cloud:**
                1. Go to your app settings
                2. Add these values in the "Secrets" section
                """,
                "severity": "critical"
            })
        
        if "DNS Resolution" in failed_tests:
            recommendations.append({
                "title": "Resolve DNS Issues",
                "content": """
                ### DNS Resolution Problems
                
                The application cannot resolve the Supabase domain name. This is common in Replit environment due to selective DNS blocking.
                
                #### Possible solutions:
                
                1. **Deploy to Streamlit Cloud**: The most reliable solution is to deploy your application to Streamlit Cloud, which does not have these DNS restrictions.
                
                2. **Use DNS Workarounds**: If you need to continue development in Replit:
                   - Try adding a hosts file entry (advanced users only)
                   - Use a proxy service to route your requests
                
                3. **Development with Sample Data**: Continue development with sample data in Replit, then deploy to Streamlit Cloud for the final version with real data.
                """,
                "severity": "high"
            })
        
        if "HTTP Connection" in failed_tests:
            recommendations.append({
                "title": "Fix Connection Issues",
                "content": """
                ### HTTP Connection Failures
                
                The application cannot establish an HTTP connection to Supabase. This could be due to:
                
                1. **Network Restrictions**: Your development environment may be blocking outbound connections
                2. **Incorrect URL**: Double-check that your SUPABASE_URL is correct
                3. **Service Outage**: Supabase might be experiencing temporary issues
                
                #### Possible solutions:
                
                1. Verify your Supabase URL in the Supabase dashboard
                2. Test if other Supabase applications are working
                3. Check the Supabase status page for outages
                """,
                "severity": "high"
            })
        
        if "REST API Test" in failed_tests or "Functions API Test" in failed_tests:
            recommendations.append({
                "title": "API Authentication Issues",
                "content": """
                ### API Authentication Problems
                
                The application is connecting to Supabase but can't authenticate. This could be due to:
                
                1. **Invalid API Key**: Your SUPABASE_KEY might be incorrect or expired
                2. **Permission Issues**: The key might not have the necessary permissions
                3. **Project Configuration**: Your Supabase project settings might be restricting access
                
                #### Possible solutions:
                
                1. Verify your API key in the Supabase dashboard
                2. Make sure you're using the service role key for full access
                3. Check Row Level Security (RLS) settings that might be blocking access
                """,
                "severity": "medium"
            })
        
        if "SQL Functions Test" in failed_tests:
            recommendations.append({
                "title": "Missing SQL Functions",
                "content": """
                ### SQL Function Problems
                
                The required SQL functions are not available or not working correctly. This could be due to:
                
                1. **Missing Functions**: The SQL functions haven't been created in your Supabase project
                2. **Function Errors**: The functions exist but have syntax or runtime errors
                3. **Permission Issues**: The functions exist but are not executable with your key
                
                #### Required SQL Functions:
                
                - `get_map_data_with_tooltips(tier_percentage, state_filter)`
                - `get_demographic_summary(tier_percentage, state_filter)`
                - `generate_market_insights(tier_percentage, state_filter, metric_column)`
                
                #### Solution:
                
                Run the SQL setup scripts from `SUPABASE_SQL_FUNCTIONS.md` in your Supabase SQL Editor to create or update these functions.
                """,
                "severity": "medium"
            })
        
        # Display recommendations with expandable sections
        for i, recommendation in enumerate(recommendations):
            severity_colors = {
                "critical": "#dc3545",  # Red
                "high": "#fd7e14",      # Orange
                "medium": "#ffc107",    # Yellow
                "low": "#28a745"        # Green
            }
            
            severity = recommendation.get("severity", "medium")
            severity_color = severity_colors.get(severity, "#6c757d")
            
            # Create a severity badge
            severity_badge = f'<span style="background-color: {severity_color}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; text-transform: uppercase;">{severity}</span>'
            
            with st.expander(f"{i+1}. {recommendation['title']} {severity_badge}", expanded=(severity == "critical")):
                st.markdown(recommendation["content"])
        
        # General deployment recommendation
        st.markdown("---")
        st.info("""
        ### 📋 General Recommendation
        
        For the most reliable operation of your DARG application with Supabase:
        
        1. Complete development in Replit with sample data fallbacks
        2. Push your code to a private GitHub repository
        3. Deploy to Streamlit Cloud with your Supabase secrets
        
        This process will ensure your application works correctly with real data in production.
        """)

# Tab 2: Advanced Diagnostics
with tab2:
    st.markdown("## Advanced Connection Diagnostics")
    
    # Host information
    hostname_input = st.text_input(
        "Target Hostname", 
        value=urlparse(os.environ.get('SUPABASE_URL', '')).netloc or "Enter Supabase hostname",
        help="Enter the hostname (domain) to analyze connection issues"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Analyze Network Path", use_container_width=True):
            if hostname_input and hostname_input != "Enter Supabase hostname":
                with st.spinner(f"Analyzing network path to {hostname_input}..."):
                    traceroute_results = traceroute(hostname_input)
                    
                    st.markdown("### Network Path Analysis")
                    for result in traceroute_results:
                        st.text(result)
            else:
                st.warning("Please enter a valid hostname to analyze")
    
    with col2:
        if st.button("Check DNS Resolvers", use_container_width=True):
            if hostname_input and hostname_input != "Enter Supabase hostname":
                with st.spinner(f"Checking DNS resolvers for {hostname_input}..."):
                    dns_resolvers = [
                        ("System DNS", lambda h: socket.gethostbyname(h)),
                        ("Google DNS (8.8.8.8)", lambda h: subprocess.run(
                            ["host", h, "8.8.8.8"], capture_output=True, text=True, timeout=5
                        ).stdout.strip()),
                        ("Cloudflare DNS (1.1.1.1)", lambda h: subprocess.run(
                            ["host", h, "1.1.1.1"], capture_output=True, text=True, timeout=5
                        ).stdout.strip())
                    ]
                    
                    st.markdown("### DNS Resolver Comparison")
                    
                    for name, resolver_func in dns_resolvers:
                        try:
                            result = resolver_func(hostname_input)
                            st.success(f"✅ {name}: Successfully resolved")
                            st.code(result)
                        except Exception as e:
                            st.error(f"❌ {name}: Failed to resolve - {str(e)}")
            else:
                st.warning("Please enter a valid hostname to check")
    
    # Function testing
    st.markdown("---")
    st.markdown("## SQL Function Testing")
    
    # Let user choose function to test
    function_options = [
        "get_map_data_with_tooltips",
        "get_demographic_summary",
        "generate_market_insights"
    ]
    
    selected_function = st.selectbox("Select SQL Function to Test", function_options)
    
    # Basic parameters
    col1, col2 = st.columns(2)
    
    with col1:
        tier_percentage = st.slider("Tier Percentage", 1, 100, 20)
    
    with col2:
        state_filter = st.multiselect(
            "State Filter", 
            options=["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"],
            default=["CA"]
        )
    
    # Additional parameters for specific functions
    if selected_function == "generate_market_insights":
        metric_column = st.selectbox(
            "Metric Column", 
            options=["market_size", "growth_rate", "accuracy", "value"],
            index=0
        )
    
    if st.button("Test Function", use_container_width=True):
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            st.error("Missing SUPABASE_URL or SUPABASE_KEY. Please set these environment variables.")
        else:
            api_url = supabase_url
            if not api_url.endswith('/rest/v1/rpc'):
                api_url = f"{api_url.rstrip('/')}/rest/v1/rpc"
            
            # Prepare parameters
            function_data = {
                "tier_percentage": tier_percentage,
                "state_filter": state_filter
            }
            
            if selected_function == "generate_market_insights":
                function_data["metric_column"] = metric_column
            
            with st.spinner(f"Testing function {selected_function}..."):
                try:
                    headers = {
                        'apikey': supabase_key,
                        'Authorization': f'Bearer {supabase_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    start_time = time.time()
                    response = requests.post(
                        f"{api_url}/{selected_function}", 
                        headers=headers,
                        json=function_data,
                        timeout=15
                    )
                    elapsed_time = time.time() - start_time
                    
                    st.markdown(f"### Function Test Results")
                    
                    # Status display
                    st.markdown(f"**Status Code:** {response.status_code}")
                    st.markdown(f"**Response Time:** {elapsed_time:.2f} seconds")
                    
                    # Header display
                    with st.expander("Response Headers"):
                        for key, value in response.headers.items():
                            st.text(f"{key}: {value}")
                    
                    # Response data
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            st.success("✅ Function returned valid JSON response")
                            
                            # Show simplified summary
                            if isinstance(data, dict):
                                st.markdown("### Response Summary")
                                
                                # Different summaries based on function
                                if selected_function == "get_map_data_with_tooltips":
                                    if "data" in data and isinstance(data["data"], list):
                                        num_locations = len(data["data"])
                                        st.markdown(f"- Returned **{num_locations}** geographic locations")
                                        
                                        if "meta" in data:
                                            for key, value in data["meta"].items():
                                                if key not in ["states"]:  # Skip arrays for brevity
                                                    st.markdown(f"- **{key}**: {value}")
                                        
                                        if num_locations > 0:
                                            st.markdown("### Sample Location")
                                            sample = data["data"][0]
                                            sample_df = pd.DataFrame([sample])
                                            st.dataframe(sample_df)
                                
                                elif selected_function == "get_demographic_summary":
                                    categories = [k for k in data.keys() if k != "meta"]
                                    st.markdown(f"- Returned demographic data for **{len(categories)}** categories")
                                    
                                    for category in categories[:3]:  # Show first 3 only
                                        if isinstance(data[category], dict):
                                            num_items = len(data[category])
                                            st.markdown(f"- **{category}**: {num_items} segments")
                                
                                elif selected_function == "generate_market_insights":
                                    if "by_state" in data and isinstance(data["by_state"], list):
                                        st.markdown(f"- State insights: **{len(data['by_state'])}** states")
                                    
                                    if "by_segment" in data and isinstance(data["by_segment"], list):
                                        st.markdown(f"- Segment insights: **{len(data['by_segment'])}** segments")
                            
                            # Full response
                            with st.expander("Full Response JSON"):
                                st.json(data)
                        except json.JSONDecodeError:
                            st.error("❌ Function returned invalid JSON response")
                            st.text(response.text)
                    else:
                        st.error(f"❌ Function call failed with status code {response.status_code}")
                        st.text(response.text)
                
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Network error: {type(e).__name__}: {str(e)}")

# Tab 3: History
with tab3:
    st.markdown("## Test History")
    
    if not st.session_state.test_history:
        st.info("No test history available yet. Run some tests to see results here.")
    else:
        # Reverse the history so newest is at the top
        for i, test_entry in enumerate(reversed(st.session_state.test_history)):
            timestamp = test_entry["timestamp"]
            results = test_entry["results"]
            duration = test_entry["duration"]
            all_passed = test_entry["all_passed"]
            
            with st.expander(f"{i+1}. Test Run: {timestamp} ({'✅ All Passed' if all_passed else '❌ Some Failed'}) - {duration:.2f}s", expanded=(i==0)):
                st.dataframe(results[["test", "status", "message"]], use_container_width=True)
    
    if len(st.session_state.test_history) > 1:
        if st.button("Clear History"):
            st.session_state.test_history = []
            st.session_state.last_test_time = None
            st.rerun()  # Updated from deprecated st.experimental_rerun()

# Tab 4: Deployment Guide
with tab4:
    st.markdown("## Deployment Guide")
    
    st.markdown("""
    ### Deploying DARG to Streamlit Cloud
    
    Follow these steps to properly deploy your DARG Market Intelligence Platform:
    
    #### 1. Prepare Your GitHub Repository
    
    1. Create a private GitHub repository
    2. Push your application code to this repository
    3. Make sure to include:
       - All application code (.py files)
       - requirements.txt with dependencies
       - .streamlit/config.toml for configuration
    
    #### 2. Set Up Streamlit Cloud
    
    1. Log in to [Streamlit Cloud](https://streamlit.io/cloud)
    2. Click "New app"
    3. Connect to your GitHub repository
    4. Configure deployment settings:
       - Main file path: `app.py`
       - Python version: 3.9 or higher
    
    #### 3. Configure Secrets
    
    In Streamlit Cloud, you'll need to set up these secrets:
    
    ```toml
    SUPABASE_URL = "https://your-project-id.supabase.co"
    SUPABASE_KEY = "your-supabase-key"
    ENVIRONMENT = "production"
    ```
    
    #### 4. Deploy and Verify
    
    1. Deploy your application
    2. Once deployed, visit the application URL
    3. Go to the Connection Status page to verify all connections work
    
    #### 5. Troubleshooting
    
    If you encounter issues:
    
    1. Check Streamlit Cloud logs for error messages
    2. Verify that your secrets are correctly set
    3. Make sure your Supabase project allows connections from Streamlit Cloud
    """)
    
    # Add links and resources
    st.markdown("---")
    st.markdown("### Helpful Resources")
    
    resources = [
        {
            "title": "Streamlit Deployment Guide",
            "url": "https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app"
        },
        {
            "title": "Supabase Documentation",
            "url": "https://supabase.io/docs"
        },
        {
            "title": "Managing Secrets in Streamlit",
            "url": "https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management"
        }
    ]
    
    for resource in resources:
        st.markdown(f"- [{resource['title']}]({resource['url']})")

# Sidebar content
st.sidebar.markdown("## Diagnostics Tools")

if st.sidebar.button("Download Diagnostic Report", use_container_width=True):
    if not st.session_state.test_history:
        st.sidebar.warning("Run tests first to generate a report")
    else:
        # Generate a simple diagnostic report
        report = "# DARG Supabase Diagnostic Report\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Environment information
        report += "## Environment Information\n\n"
        report += f"- Environment: {os.environ.get('ENVIRONMENT', 'development')}\n"
        
        # Add the latest test results
        last_test = st.session_state.test_history[-1]
        report += "\n## Latest Test Results\n\n"
        report += f"- Timestamp: {last_test['timestamp']}\n"
        report += f"- Duration: {last_test['duration']:.2f} seconds\n"
        report += f"- All Tests Passed: {last_test['all_passed']}\n\n"
        
        # Add test details
        report += "### Test Details\n\n"
        for _, row in last_test["results"].iterrows():
            report += f"- **{row['test']}**: {row['status']}\n"
            report += f"  {row['message']}\n\n"
        
        # Convert to download link
        from base64 import b64encode
        b64_report = b64encode(report.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64_report}" download="darg_diagnostic_report.md">Click to download diagnostic report</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)
        st.sidebar.success("Report generated successfully!")

# Tier status indicator in sidebar
current_tier = get_user_tier()
tier_labels = {"Free": "🔹", "Accelerate": "🔸", "Scale": "⭐"}
st.sidebar.markdown("---")
st.sidebar.markdown(f"### Current Tier: {tier_labels.get(current_tier, '🔹')} {current_tier}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888;">
© 2023 DARG Market Intelligence Platform. All rights reserved.
</div>
""", unsafe_allow_html=True)
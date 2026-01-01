import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

API_BASE_URL = "http://localhost:5000/api"

st.set_page_config(
    page_title="Clinical Supply Chain Control Tower",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Clinical Supply Chain Control Tower")
st.markdown("Multi-Agent AI System for Clinical Supply Chain Management")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["System Health", "Agent Query", "SQL Query", "Audit Logs", "About"]
)

def check_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def execute_sql(query):
    try:
        response = requests.post(
            f"{API_BASE_URL}/sql",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def process_query(query):
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

if page == "System Health":
    st.header("System Health Check")
    
    if st.button("Check Backend Status", type="primary"):
        with st.spinner("Checking backend status..."):
            result, status_code = check_health()
            
            if status_code == 200:
                st.success("Backend is running successfully!")
                st.json(result)
            else:
                st.error("Backend connection failed!")
                st.json(result)
    
    st.divider()
    
    st.subheader("System Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("API Endpoint", "localhost:5000")
    with col2:
        st.metric("Status", "Active" if check_health()[1] == 200 else "Inactive")
    with col3:
        st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    st.subheader("Available Endpoints")
    endpoints = [
        {"Method": "GET", "Endpoint": "/api/health", "Description": "Health check"},
        {"Method": "POST", "Endpoint": "/api/query", "Description": "Process agent query"},
        {"Method": "POST", "Endpoint": "/api/sql", "Description": "Execute SQL query"},
        {"Method": "GET", "Endpoint": "/api/watchdog/run", "Description": "Run watchdog"}
    ]
    st.table(pd.DataFrame(endpoints))

elif page == "Agent Query":
    st.header("AI Agent Query Interface")
    st.markdown("Ask questions in natural language and let the AI agents analyze the data.")
    
    st.divider()
    
    example_queries = [
        "Can we extend expiry of Batch #123 for the German trial?",
        "Check shipping timelines for Saint Kitts and Nevis",
        "Verify regulatory approval status for Germany",
        "Check stability data for batch #123"
    ]
    
    st.subheader("Example Queries")
    selected_example = st.selectbox("Select an example query:", [""] + example_queries)
    
    user_query = st.text_area(
        "Enter your query:",
        value=selected_example if selected_example else "",
        height=100,
        placeholder="Type your question here..."
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        query_button = st.button("Submit Query", type="primary", disabled=not user_query)
    with col2:
        clear_button = st.button("Clear")
        
    if clear_button:
        st.rerun()
    
    if query_button and user_query:
        with st.spinner("Processing query through AI agents..."):
            result, status_code = process_query(user_query)
            
            if status_code == 200 and "error" not in result:
                st.success("Query processed successfully!")
                
                st.divider()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    severity = result.get("severity", "N/A")
                    color = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡"
                    }.get(severity, "⚪")
                    st.metric("Severity", f"{color} {severity}")
                
                with col2:
                    decision = result.get("decision", "N/A")
                    st.metric("Decision", decision)
                
                with col3:
                    risk_type = result.get("risk_type", "N/A")
                    st.metric("Risk Type", risk_type)
                
                st.divider()
                
                if result.get("weeks_of_cover"):
                    st.info(f"📊 Weeks of Cover: {result['weeks_of_cover']}")
                
                st.subheader("Analysis & Reasoning")
                reasoning = result.get("reasoning", {})
                
                tab1, tab2, tab3 = st.tabs(["Technical", "Regulatory", "Logistical"])
                
                with tab1:
                    st.write(reasoning.get("technical", "N/A"))
                
                with tab2:
                    st.write(reasoning.get("regulatory", "N/A"))
                
                with tab3:
                    st.write(reasoning.get("logistical", "N/A"))
                
                st.divider()
                
                st.subheader("Recommended Action")
                st.warning(result.get("recommended_action", "No action specified"))
                
                st.divider()
                
                st.subheader("Source Tables")
                source_tables = result.get("source_tables", [])
                if source_tables:
                    st.code(", ".join(source_tables))
                else:
                    st.write("No source tables specified")
                
                if "uncertainty" in result:
                    st.error(f"⚠️ Uncertainty: {result['uncertainty']}")
                
                st.divider()
                
                st.subheader("📄 Complete JSON Response")
                st.json(result)
                
                st.divider()
                
                with st.expander("📋 Copy as JSON"):
                    st.code(json.dumps(result, indent=2), language="json")
            else:
                st.error("Query processing failed!")
                st.json(result) 

elif page == "SQL Query":
    st.header("Direct SQL Query Interface")
    st.markdown("Execute read-only SELECT queries on the clinical supply database.")
    
    st.warning("⚠️ Only SELECT queries are allowed. Write operations are prohibited.")
    
    st.divider()
    
    example_queries_sql = {
        "Available Inventory": "SELECT * FROM available_inventory_report LIMIT 10",
        "Enrollment Rates": "SELECT * FROM enrollment_rate_report LIMIT 10",
        "Shipping Timelines": "SELECT * FROM ip_shipping_timelines_report LIMIT 10",
        "Regulatory Status": "SELECT * FROM rim LIMIT 10",
        "Batch Re-evaluation": "SELECT * FROM \"re-evaluation\" LIMIT 10"
    }
    
    st.subheader("Example Queries")
    selected_example = st.selectbox("Select an example:", ["Custom Query"] + list(example_queries_sql.keys()))
    
    if selected_example != "Custom Query":
        default_query = example_queries_sql[selected_example]
    else:
        default_query = ""
    
    sql_query = st.text_area(
        "SQL Query:",
        value=default_query,
        height=150,
        placeholder="SELECT * FROM available_inventory_report LIMIT 10"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        execute_button = st.button("Execute Query", type="primary", disabled=not sql_query)
    with col2:
        clear_sql_button = st.button("Clear Query")
    
    if clear_sql_button:
        st.rerun()
    
    if execute_button and sql_query:
        if not sql_query.strip().upper().startswith("SELECT"):
            st.error("Only SELECT queries are allowed!")
        else:
            with st.spinner("Executing query..."):
                result, status_code = execute_sql(sql_query)
                
                if status_code == 200 and result.get("success"):
                    st.success(f"Query executed successfully! ({result.get('row_count', 0)} rows)")
                    
                    data = result.get("data", [])
                    
                    if data:
                        df = pd.DataFrame(data)
                        
                        st.divider()
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader("Query Results")
                        with col2:
                            st.metric("Total Rows", len(df))
                        
                        st.dataframe(df, use_container_width=True)
                        
                        st.divider()
                        
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download as CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                        with st.expander("View Raw JSON"):
                            st.json(data)
                    else:
                        st.info("Query returned no results.")
                else:
                    st.error("Query execution failed!")
                    st.json(result)

elif page == "Audit Logs":
    st.header("AI Decision Audit Logs")
    st.markdown("View logged decisions made by the AI agents.")
    
    st.divider()
    
    audit_query = """
    SELECT 
        id,
        decision_type,
        decision_json->>'severity' as severity,
        decision_json->>'decision' as decision,
        source_tables,
        timestamp
    FROM ai_decisions
    ORDER BY timestamp DESC
    LIMIT 20
    """
    
    if st.button("Load Recent Decisions", type="primary"):
        with st.spinner("Loading audit logs..."):
            result, status_code = execute_sql(audit_query)
            
            if status_code == 200 and result.get("success"):
                data = result.get("data", [])
                
                if data:
                    df = pd.DataFrame(data)
                    
                    st.subheader(f"Last {len(df)} Decisions")
                    
                    for idx, row in df.iterrows():
                        with st.expander(
                            f"Decision #{row['id']} - {row['decision_type']} - {row['timestamp']}"
                        ):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Decision", row['decision'])
                            with col2:
                                st.metric("Severity", row['severity'])
                            with col3:
                                st.metric("Type", row['decision_type'])
                            
                            st.write("**Source Tables:**")
                            st.code(row['source_tables'])
                    
                    st.divider()
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Audit Logs",
                        data=csv,
                        file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No audit logs found.")
            else:
                st.error("Failed to load audit logs!")
                st.json(result)
    
    st.divider()
    
    st.subheader("Custom Audit Query")
    custom_audit_query = st.text_area(
        "Advanced Query:",
        value="SELECT * FROM ai_decisions ORDER BY timestamp DESC LIMIT 10",
        height=100
    )
    
    if st.button("Execute Custom Audit Query"):
        with st.spinner("Executing query..."):
            result, status_code = execute_sql(custom_audit_query)
            
            if status_code == 200 and result.get("success"):
                data = result.get("data", [])
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
                else:
                    st.info("No results found.")
            else:
                st.error("Query failed!")
                st.json(result)

elif page == "About":
    st.header("About Clinical Supply Chain Control Tower")
    
    st.markdown("""
    ### Overview
    
    The Clinical Supply Chain Control Tower is a **Multi-Agent AI System** designed to autonomously 
    monitor and analyze clinical supply chain risks.
    
    ### Key Features
    
    - **Multi-Agent Architecture**: Specialized agents for different domains
    - **Real-time Analysis**: Inventory, demand, logistics, regulatory, and QA monitoring
    - **Autonomous Decision Making**: AI-driven risk detection and recommendations
    - **Auditable**: All decisions logged for compliance
    - **Natural Language Interface**: Ask questions in plain English
    
    """)
    
    st.divider()
    
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Backend Connection"):
            result, status = check_health()
            if status == 200:
                st.success("✅ Backend is running!")
            else:
                st.error("❌ Backend is not responding!")
    
    with col2:
        if st.button("View System Status"):
            st.info("Navigate to System Health page")
    
    with col3:
        if st.button("Start Agent Query"):
            st.info("Navigate to Agent Query page")

st.sidebar.divider()
st.sidebar.markdown("### System Status")
health_result, health_status = check_health()
if health_status == 200:
    st.sidebar.success("✅ Backend Online")
else:
    st.sidebar.error("❌ Backend Offline")

st.sidebar.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
